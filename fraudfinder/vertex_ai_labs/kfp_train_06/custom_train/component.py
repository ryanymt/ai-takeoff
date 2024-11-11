from typing import List

from kfp import dsl
from google_cloud_pipeline_components.types import artifact_types

from ..conf import vertex_config


@dsl.component(
    base_image=vertex_config.BASE_IMAGE,
    packages_to_install=[
        "gcsfs==2024.10.0",
        "numpy==1.26.4", 
        "pandas==2.2.3", 
        "scikit-learn==1.5.2", 
        "dask==2024.10.0", 
        "dask-ml==2024.4.4",
        "distributed==2024.10.0", 
        "xgboost==2.1.2",
        "google-cloud-pipeline-components==2.17.0",
        "google-cloud-aiplatform==1.71.0",
    ]
)
def train_model(
    project: str,
    location: str,
    bucket: str,
    dataset: dsl.Input[artifact_types.VertexDataset],
    dtype: dict,
    drop_cols: List[str],
    target_col: str,
    feat_cols: List[str],
    model_reg: str,
    trained_model: dsl.Output[artifact_types.VertexModel],
    test_ds: dsl.Output[dsl.Dataset],
):
    from typing import List
    from pathlib import Path
    from datetime import datetime, timezone
    import dask.dataframe as dask_df
    from dask_ml.model_selection import train_test_split
    from dask.distributed import LocalCluster, Client
    import xgboost as xgb
    from google.cloud import aiplatform as vertex_ai


    ## Read environmental variables
    def gcs_path_to_local_path(old_path: str) -> str:
        new_path = old_path.replace("gs://", "/gcs/")
        return new_path

    ## Training variables
    N_PARTITIONS = 4

    vertex_ai.init(project=project, location=location, staging_bucket=f"gs://{bucket}")

    # manually extract and split 
    dataset_id = dataset.metadata['resourceName'].split("/")[-1]
    dataset = vertex_ai.TabularDataset(dataset.metadata['resourceName'])
    dataset_uris = dataset.gca_resource.metadata['inputConfig']['gcsSource']['uri']
    dataset_uris = [gcs_path_to_local_path(dataset_uri) for dataset_uri in dataset_uris]
    ds_df = dask_df.read_csv(dataset_uris, dtype=dtype)
    train_df, test_df = train_test_split(ds_df, test_size=0.2, shuffle=True)
    eval_df, test_df = train_test_split(test_df, test_size=0.5)
    TRAINING_DIR = (
        f"/gcs/{bucket}/aiplatform-custom-training-"
        f"{datetime.now(timezone.utc).strftime('%Y-%m-%d-%H:%M:%S.%f')}"
    )
    TRAINING_DATA_DIR = (
        f"{TRAINING_DIR}/dataset-{dataset_id}-tables-"
        f"{datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%fZ')}"
    )
    TRAINING_DATA_PATH = f"{TRAINING_DATA_DIR}/training-0000*-of-0000{N_PARTITIONS}.csv"
    EVAL_DATA_PATH = f"{TRAINING_DATA_DIR}/validation-0000*-of-0000{N_PARTITIONS}.csv"
    TEST_DATA_PATH = f"{TRAINING_DATA_DIR}/test-0000*-of-0000{N_PARTITIONS}.csv"
    train_df.repartition(npartitions=N_PARTITIONS).to_csv(TRAINING_DATA_PATH)
    eval_df.repartition(npartitions=N_PARTITIONS).to_csv(EVAL_DATA_PATH)
    test_df.repartition(npartitions=N_PARTITIONS).to_csv(TEST_DATA_PATH)

    MODEL_DIR = f"{TRAINING_DIR}/model"
    MODEL_PATH = f"{MODEL_DIR}/model.bst"


    def resample(df: dask_df.DataFrame, replace: bool, frac: float = 1, random_state: int = 8) -> dask_df.DataFrame:
        shuffled_df = df.sample(frac=frac, replace=replace, random_state=random_state)
        return shuffled_df

    def preprocess(df: dask_df.DataFrame, drop_cols: List[str] = None) -> dask_df.DataFrame:
        if drop_cols:
            df = df.drop(columns=drop_cols)

        # Drop rows with NaN"s
        df = df.dropna()

        # Convert integer valued (numeric) columns to floating point
        numeric_columns = df.select_dtypes(["float32", "float64"]).columns
        numeric_format = {col:"float32" for col in numeric_columns}
        df = df.astype(numeric_format)

        return df

    
    # preprocessing
    preprocessed_train_df = preprocess(train_df, drop_cols)
    preprocessed_test_df = preprocess(test_df, drop_cols)
    
    # downsampling
    train_nfraud_df = preprocessed_train_df[preprocessed_train_df[target_col]==0]
    train_fraud_df = preprocessed_train_df[preprocessed_train_df[target_col]==1]
    train_nfraud_downsample = resample(
        train_nfraud_df,
        replace=True, 
        frac=len(train_fraud_df)/len(train_df)
    )
    ds_preprocessed_train_df = dask_df.concat([train_nfraud_downsample, train_fraud_df])
    
    # target, features split
    x_train = ds_preprocessed_train_df[feat_cols].values
    y_train = ds_preprocessed_train_df.loc[:, target_col].astype(int).values
    x_true = preprocessed_test_df[feat_cols].values
    y_true = preprocessed_test_df.loc[:, target_col].astype(int).values
    preprocessed_test_df.to_csv(test_ds.path)
    
    # train model
    cluster =  LocalCluster()
    client = Client(cluster)
    model = xgb.dask.DaskXGBClassifier(objective="reg:logistic", eval_metric="logloss")
    model.client = client
    model.fit(x_train, y_train, eval_set=[(x_true, y_true)])
    if not Path(MODEL_DIR).exists():
        Path(MODEL_DIR).mkdir(parents=True, exist_ok=True)
    model.save_model(MODEL_PATH)
    # upload model
    vertex_ai_model = vertex_ai.Model.upload_xgboost_model_file(
        xgboost_version="1.7",
        model_file_path=MODEL_PATH,
        display_name=model_reg,
    )
    trained_model.uri = vertex_ai_model.uri
    trained_model.metadata["resourceName"] = vertex_ai_model.resource_name
    trained_model.metadata["path"] = MODEL_PATH
    print(trained_model.metadata)
    print(trained_model.path, trained_model.uri)
