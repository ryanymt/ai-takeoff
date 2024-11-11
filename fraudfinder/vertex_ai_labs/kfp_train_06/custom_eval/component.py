from kfp import dsl
from typing import NamedTuple
from google_cloud_pipeline_components.types import artifact_types

from fraudfinder.vertex_ai_labs.kfp_train_06 import vertex_config


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
    ],
)
def evaluate_model(
    threshold: float,
    model_in: dsl.Input[artifact_types.VertexModel],
    test_ds: dsl.Input[dsl.Dataset],
    metrics_uri: str,
) -> NamedTuple(
    "outputs",
    meta_metrics=dsl.Metrics,
    graph_metrics=dsl.ClassificationMetrics,
    avg_prec=float,
):
    # Libraries --------------------------------------------------------------------------------------------------------------------------
    import json
    import dask.dataframe as dask_df
    import numpy as np
    import xgboost as xgb
    import dask.dataframe as dask_df
    from sklearn.metrics import (confusion_matrix, average_precision_score, f1_score, 
                                log_loss, precision_score, recall_score)


    def evaluate_model_fn(model: xgb.Booster, x_true: np.ndarray, y_true: np.ndarray, threshold: float = 0.5) -> dict:
        #calculate metrics
        metrics={}
        x_true = xgb.DMatrix(x_true)
        y_score = model.predict(x_true)
        y_pred = np.where(y_score >= threshold, 1, 0)
        c_matrix = confusion_matrix(y_true, y_pred)
        
        avg_precision_score = round(average_precision_score(y_true, y_score), 3)
        f1 = round(f1_score(y_true, y_pred), 3)
        lg_loss = round(log_loss(y_true, y_pred), 3)
        prec_score = round(precision_score(y_true, y_pred), 3)
        rec_score = round(recall_score(y_true, y_pred), 3)
        
        metrics["confusion_matrix"] = c_matrix.tolist()
        metrics["avg_precision_score"] = avg_precision_score
        metrics["f1_score"] = f1
        metrics["log_loss"] = lg_loss
        metrics["precision_score"] = prec_score
        metrics["recall_score"] = rec_score
        
        return metrics


    # load the dataframe, dask save to path as folder, need to put wildcard
    print("eval", test_ds.path)
    print("eval", model_in.path)
    test_df = dask_df.read_csv(f"{test_ds.path}/*", dtype=vertex_config.DATA_SCHEMA)
    test_df = test_df.compute()
    model = xgb.Booster()
    model.load_model(model_in.metadata["path"])
    eval_metrics = evaluate_model_fn(model, test_df[vertex_config.FEAT_COLUMNS], test_df[vertex_config.TARGET_COLUMN], threshold=threshold)

    # Variables --------------------------------------------------------------------------------------------------------------------------
    metrics_path = metrics_uri.replace("gs://", "/gcs/")
    labels = ["not fraud", "fraud"]

    # Main -------------------------------------------------------------------------------------------------------------------------------
    with open(metrics_path, mode="w") as metrics_file:
        json.dump(eval_metrics, metrics_file, indent=2)

    ## metrics
    c_matrix = eval_metrics["confusion_matrix"]
    avg_precision_score = eval_metrics["avg_precision_score"]
    f1 = eval_metrics["f1_score"]
    lg_loss = eval_metrics["log_loss"]
    prec_score = eval_metrics["precision_score"]
    rec_score = eval_metrics["recall_score"]

    meta_metrics = dsl.Metrics()
    meta_metrics.log_metric("avg_precision_score", avg_precision_score)
    meta_metrics.log_metric("f1_score", f1)
    meta_metrics.log_metric("log_loss", lg_loss)
    meta_metrics.log_metric("precision_score", prec_score)
    meta_metrics.log_metric("recall_score", rec_score)
    graph_metrics = dsl.ClassificationMetrics()
    graph_metrics.log_confusion_matrix(labels, c_matrix)


    ## model metadata
    # model_out.metadata["framework"] = "xgb.dask"
    # model_out.metadata["algorithm"] = "DaskXGBClassifier"
    # model_out.metadata["type"] = "classification"
    print("metadata metrics", meta_metrics.metadata)
    print("graph metrics", graph_metrics.metadata)

    eval_output = NamedTuple(
        "outputs",
        meta_metrics=dsl.Metrics,
        graph_metrics=dsl.ClassificationMetrics,
        avg_prec=float, 
    )
    return eval_output(
        meta_metrics=meta_metrics,
        graph_metrics=graph_metrics,
        avg_prec=avg_precision_score,
    )
