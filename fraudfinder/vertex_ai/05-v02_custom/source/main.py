"""
In progress, still have errors. :(
"""

import os
from google.cloud import bigquery
from google.cloud import aiplatform as vertex_ai
from datetime import datetime, timedelta
import time
from utils import (
    load_environment_variables_from_gcs,
    get_gcp_project,
    run_bq_query,
    preprocess,
    train_and_evaluate_model,
    save_model_to_gcs,
    fetch_features_from_featurestore,
)

if __name__ == "__main__":
    # Get GCP project ID
    GCP_PROJECT = get_gcp_project()
    PROJECT_ID = GCP_PROJECT

    #  Load environment variables
    BUCKET_NAME = f"{PROJECT_ID}-fraudfinder"
#    load_environment_variables_from_gcs(BUCKET_NAME, "config/notebook_env_v02.py")

# test 
    config_vars = load_environment_variables_from_gcs(
       f"{BUCKET_NAME}", "config/notebook_env_v02.py"
    )  # Get the variables

    # Print and use the variables
    print("\nEnvironment variables:")
    for key, value in config_vars.items():
        if not key.startswith("_"):
            print(f"  {key}: {value}")
            globals()[key] = value  # Add to global scope in main.py






    #Featurestore
    START_DATE_TRAIN = (datetime.today() - timedelta(days=1)).strftime("%Y-%m-%d")
    END_DATE_TRAIN = (datetime.today() - timedelta(days=1)).strftime("%Y-%m-%d")
    CUSTOMER_ENTITY = "customer"
    TERMINAL_ENTITY = "terminal"
    SERVING_FEATURE_IDS = {CUSTOMER_ENTITY: ["*"], TERMINAL_ENTITY: ["*"]}
    READ_INSTANCES_TABLE = f"ground_truth_{END_DATE_TRAIN}"
    READ_INSTANCES_URI = f"bq://{PROJECT_ID}.tx.{READ_INSTANCES_TABLE}"

    #  Initialize Vertex AI
    vertex_ai.init(
        project=GCP_PROJECT,
        location=REGION,
        staging_bucket=BUCKET_NAME, 
    )

    #  Construct BigQuery SQL query (for base data)
    query = f"""
        SELECT
            raw_tx.TX_TS AS timestamp,
            raw_tx.CUSTOMER_ID AS customer,  
            raw_tx.TERMINAL_ID AS terminal, 
            raw_tx.TX_AMOUNT AS tx_amount,
            raw_lb.TX_FRAUD AS tx_fraud,
        FROM
            tx.tx AS raw_tx  
        LEFT JOIN
            tx.txlabels AS raw_lb  
        ON raw_tx.TX_ID = raw_lb.TX_ID
        WHERE
            DATE(raw_tx.TX_TS) = "{START_DATE_TRAIN}";
    """

    #  Fetch base data from BigQuery
    base_df = run_bq_query(query)

    #  Fetch features from Feature Store
    df = fetch_features_from_featurestore(base_df)

    #  Preprocess data
    df = preprocess(df)

    # 8. Train and evaluate model
    model, metrics = train_and_evaluate_model(df, TARGET)

    # 9. Save the model
    model_bucket = "model-upload-2808"
    model_path = "models/model.bst"
    save_model_to_gcs(model, model_bucket, "model.bst") 

