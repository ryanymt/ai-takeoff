import os
import json
import yaml
from pathlib import Path
import dask.dataframe as dask_df
from dask.distributed import LocalCluster, Client
import xgboost as xgb
from utils import gcs_path_to_local_path, resample, preprocess, evaluate_model


with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

TRAINING_DATA_PATH = gcs_path_to_local_path(os.environ["AIP_TRAINING_DATA_URI"])
TEST_DATA_PATH = gcs_path_to_local_path(os.environ["AIP_TEST_DATA_URI"])
MODEL_DIR = gcs_path_to_local_path(os.environ["AIP_MODEL_DIR"])
MODEL_PATH = MODEL_DIR + "model.bst"

## Training variables
LABEL_COLUMN = "tx_fraud"
FEAT_COLUMNS = [
    'customer_id_avg_amount_14day_window', 
    'customer_id_avg_amount_15min_window', 
    'customer_id_avg_amount_1day_window', 
    'customer_id_avg_amount_30min_window', 
    'customer_id_avg_amount_60min_window', 
    'customer_id_avg_amount_7day_window', 
    'customer_id_nb_tx_14day_window', 
    'customer_id_nb_tx_15min_window', 
    'customer_id_nb_tx_1day_window', 
    'customer_id_nb_tx_30min_window', 
    'customer_id_nb_tx_60min_window', 
    'customer_id_nb_tx_7day_window', 
    'terminal_id_avg_amount_15min_window', 
    'terminal_id_avg_amount_30min_window', 
    'terminal_id_avg_amount_60min_window', 
    'terminal_id_nb_tx_14day_window', 
    'terminal_id_nb_tx_15min_window', 
    'terminal_id_nb_tx_1day_window', 
    'terminal_id_nb_tx_30min_window', 
    'terminal_id_nb_tx_60min_window', 
    'terminal_id_nb_tx_7day_window', 
    'terminal_id_risk_14day_window', 
    'terminal_id_risk_1day_window', 
    'terminal_id_risk_7day_window', 
    'tx_amount'
]
UNUSED_COLUMNS = ["timestamp", "entity_type_customer", "entity_type_terminal"]
DATA_SCHEMA = {
"timestamp" : "object",
"tx_amount": "float64",
"tx_fraud": "Int64",
"entity_type_customer": "Int64",
"customer_id_nb_tx_1day_window": "Int64",
"customer_id_nb_tx_7day_window": "Int64",
"customer_id_nb_tx_14day_window": "Int64",
"customer_id_avg_amount_1day_window": "float64",
"customer_id_avg_amount_7day_window": "float64",
"customer_id_avg_amount_14day_window": "float64",
"customer_id_nb_tx_15min_window": "Int64",
"customer_id_avg_amount_15min_window": "float64",
"customer_id_nb_tx_30min_window": "Int64",
"customer_id_avg_amount_30min_window": "float64",
"customer_id_nb_tx_60min_window": "Int64",
"customer_id_avg_amount_60min_window": "float64",
"entity_type_terminal": "Int64",
"terminal_id_nb_tx_1day_window": "Int64",
"terminal_id_nb_tx_7day_window": "Int64",
"terminal_id_nb_tx_14day_window": "Int64",
"terminal_id_risk_1day_window": "float64",
"terminal_id_risk_7day_window": "float64",
"terminal_id_risk_14day_window": "float64",
"terminal_id_nb_tx_15min_window": "Int64",
"terminal_id_avg_amount_15min_window": "float64",
"terminal_id_nb_tx_30min_window": "Int64",
"terminal_id_avg_amount_30min_window": "float64",
"terminal_id_nb_tx_60min_window": "Int64",
"terminal_id_avg_amount_60min_window": "float64"
}


def main():
    # variables
    bucket = gcs_path_to_local_path(config["BUCKET_NAME"])
    deliverable_uri = (Path(bucket)/"deliverables")
    metrics_uri = (deliverable_uri/"metrics.json")

    # read data
    train_df = dask_df.read_csv(TRAINING_DATA_PATH, dtype=DATA_SCHEMA)
    test_df = dask_df.read_csv(TEST_DATA_PATH, dtype=DATA_SCHEMA)
    
    # preprocessing
    preprocessed_train_df = preprocess(train_df, UNUSED_COLUMNS)
    preprocessed_test_df = preprocess(test_df, UNUSED_COLUMNS)
    
    # downsampling
    train_nfraud_df = preprocessed_train_df[preprocessed_train_df[LABEL_COLUMN]==0]
    train_fraud_df = preprocessed_train_df[preprocessed_train_df[LABEL_COLUMN]==1]
    train_nfraud_downsample = resample(train_nfraud_df, replace=True, frac=len(train_fraud_df)/len(train_df))
    ds_preprocessed_train_df = dask_df.concat([train_nfraud_downsample, train_fraud_df])
    
    # target, features split
    x_train = ds_preprocessed_train_df[FEAT_COLUMNS].values
    y_train = ds_preprocessed_train_df.loc[:, LABEL_COLUMN].astype(int).values
    x_true = preprocessed_test_df[FEAT_COLUMNS].values
    y_true = preprocessed_test_df.loc[:, LABEL_COLUMN].astype(int).values
    
    # train model
    cluster =  LocalCluster()
    client = Client(cluster)
    model = xgb.dask.DaskXGBClassifier(objective="reg:logistic", eval_metric="logloss")
    model.client = client
    model.fit(x_train, y_train, eval_set=[(x_true, y_true)])
    if not Path(MODEL_DIR).exists():
        Path(MODEL_DIR).mkdir(parents=True, exist_ok=True)
    model.save_model(MODEL_PATH)
    
    #generate metrics
    metrics = evaluate_model(model, x_true, y_true)
    if not Path(deliverable_uri).exists():
        Path(deliverable_uri).mkdir(parents=True, exist_ok=True)
    with open(metrics_uri, "w") as file:
        json.dump(metrics, file, sort_keys = True, indent = 4)


main()
