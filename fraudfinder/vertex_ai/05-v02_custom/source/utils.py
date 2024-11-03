import google.cloud.storage as storage
from google.cloud import bigquery
import pandas as pd
from google.cloud.aiplatform import Featurestore
import random
import subprocess
import os

# model training imports
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
    average_precision_score,
    log_loss,
    precision_score,
    recall_score,
)
###

def load_environment_variables_from_gcs01(bucket_name, file_path):
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(file_path)
    config_file_content = blob.download_as_string().decode("utf-8")

    # Execute the content of the config file in a local dictionary
    local_vars = {}
    exec(config_file_content, globals(), local_vars)

    
    # Declare all variables in the config file as global
    globals().update({key: value for key, value in local_vars.items() if not key.startswith("_")}) 

def load_environment_variables_from_gcs(bucket_name, file_path):
    """
    Loads environment variables from a Python file in a GCS bucket.
    Returns a dictionary containing the loaded variables.
    """
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(file_path)
    config_file_content = blob.download_as_string().decode("utf-8")

    local_vars = {}
    exec(config_file_content, globals(), local_vars)
    return local_vars  # Return the variables

  
def load_environment_variables_from_gcs02(bucket_name, file_path):
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(file_path)
    config_file_content = blob.download_as_string().decode("utf-8")

    # Execute the content of the config file in a local dictionary
    local_vars = {}
    exec(config_file_content, globals(), local_vars)

    # Set environment variables from the local dictionary
    for key, value in local_vars.items():
        if not key.startswith("_"):  # Exclude internal variables
            os.environ[key] = str(value)  # Ensure value is a string
   #         print(f"  {key}: {value}")
    # Update global variables with values from the config file
    globals().update({key: value for key, value in local_vars.items() if not key.startswith("_")})



def get_gcp_project():
    """Retrieves the currently active GCP project ID.
    """
    try:
        process = subprocess.run(['gcloud', 'config', 'get-value', 'project'], capture_output=True, text=True)
        project_id = process.stdout.strip()
        return project_id
    except FileNotFoundError:
        print("gcloud CLI not found. Please install and configure it.")
        return None
    

def run_bq_query(sql: str) -> pd.DataFrame:

    bq_client = bigquery.Client()

    # Try dry run before executing query to catch any errors
    job_config = bigquery.QueryJobConfig(dry_run=True, use_query_cache=False)
    bq_client.query(sql, job_config=job_config)

    # If dry run succeeds without errors, proceed to run query
    job_config = bigquery.QueryJobConfig()
    client_result = bq_client.query(sql, job_config=job_config)

    job_id = client_result.job_id

    # Wait for query/job to finish running. then get & return data frame
    df = client_result.result().to_arrow().to_pandas()
    print(f"Finished job_id: {job_id}")
    return df

def preprocess(df: pd.DataFrame):
    """
    Converts categorical features to numeric. Removes unused columns.
    """
    UNUSED_COLUMNS = ["timestamp", "entity_type_customer", "entity_type_terminal"]
    df = df.drop(columns=UNUSED_COLUMNS)

    # Drop rows with NaN"s
    df = df.dropna()

    # Convert integer valued (numeric) columns to floating point
    numeric_columns = df.select_dtypes(["int32", "float32", "float64"]).columns
    df[numeric_columns] = df[numeric_columns].astype("float32")

    # Convert tx_amount to numeric
    df['tx_amount'] = pd.to_numeric(df['tx_amount']) 

    dummy_columns = list(df.dtypes[df.dtypes == "category"].index)
    df = pd.get_dummies(df, columns=dummy_columns)

    return df


def train_and_evaluate_model(df: pd.DataFrame, target_column: str):
    """
    Trains an XGBoost model, evaluates it, and returns the model and metrics.

    Args:
        df: DataFrame containing the preprocessed data.

    Returns:
        model: The trained XGBoost model.
        metrics: A dictionary of evaluation metrics.
    """

    # Split data into features and target
    X = df.drop(columns=[target_column])  
    y = df[target_column]

    # Split data into train and test sets
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42

    )

    # Initialize and train the XGBoost model
    model = xgb.XGBClassifier(

        objective="binary:logistic",  # Using binary classification objective
        random_state=42,
    )
    model.fit(X_train, y_train)

    # Make predictions
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]

    # Calculate evaluation metrics
    metrics = {
        "accuracy": accuracy_score(y_test, y_pred),
        "f1_score": f1_score(y_test, y_pred),
        "roc_auc": roc_auc_score(y_test, y_prob),
        "confusion_matrix": confusion_matrix(y_test, y_pred).tolist(),
        "average_precision": average_precision_score(y_test, y_prob),
        "log_loss": log_loss(y_test, y_prob),
        "precision": precision_score(y_test, y_pred),
        "recall": recall_score(y_test, y_pred),
    }

    return model, metrics


def save_model_to_gcs(model, bucket_name, model_path):
    """Saves a model to a GCS bucket.
    """
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(model_path)

    # Save the model to a temporary file
    #debug
    print(f"Saving model to: gs://{bucket_name}/{model_path}")
    temp_file = "/tmp/model.bst"
    model.save_model(temp_file)
    # debug
    print(os.path.exists(temp_file))

    # Upload the temporary file to GCS
    blob.upload_from_filename(temp_file)
    #debug
    print(blob.public_url)


def fetch_features_from_featurestore(base_df: pd.DataFrame) -> pd.DataFrame:
    """
    Fetches features from the Feature Store based on entity IDs in base_df.
    """
    ####
    # Temp Code. ID was random generated number. Will fix that part and remove this hardcode. 
    ####
    FEATURESTORE_ID      = "fraudfinder_fvde2"
    ####
    featurestore = Featurestore(FEATURESTORE_ID)

    # Assuming your base_df has "customer" and "terminal" columns for entity IDs
    serving_feature_ids = {
        "customer": ["*"],  # Fetch all features for customer entity
        "terminal": ["*"],  # Fetch all features for terminal entity
    }

    df = featurestore.batch_serve_to_df(
        serving_feature_ids=serving_feature_ids,
        read_instances_df=base_df,
        pass_through_fields=["tx_fraud", "tx_amount"],  # Include original fields
    )
    return df
