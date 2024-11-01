from typing import List, Union
import numpy as np
import dask.dataframe as dask_df
import xgboost as xgb
from sklearn.metrics import (roc_curve, confusion_matrix, average_precision_score, f1_score, 
                            log_loss, precision_score, recall_score)


def gcs_path_to_local_path(old_path: str) -> str:
    """convert GCS path to local path

    Args:
        old_path (str): GCS path

    Returns:
        str: local path
    """
    if old_path.startswith("gs://"):
        new_path = old_path.replace("gs://", "/gcs/")
    else:
        new_path = f"/gcs/{old_path}"
    return new_path


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


def evaluate_model(model: xgb.Booster, x_true: Union[dask_df.DataFrame, np.ndarray], y_true: Union[dask_df.Series, np.ndarray]) -> dict:
    y_true = y_true.compute()
    
    #calculate metrics
    metrics={}
    
    y_score =  model.predict_proba(x_true)[:, 1]
    y_score = y_score.compute()
    fpr, tpr, thr = roc_curve(
         y_true=y_true, y_score=y_score, pos_label=True
    )
    fpr_list = fpr.tolist()[::1000]
    tpr_list = tpr.tolist()[::1000]
    thr_list = thr.tolist()[::1000]

    y_pred = model.predict(x_true)
    y_pred = y_pred.compute()
    c_matrix = confusion_matrix(y_true, y_pred)
    
    avg_precision_score = round(average_precision_score(y_true, y_score), 3)
    f1 = round(f1_score(y_true, y_pred), 3)
    lg_loss = round(log_loss(y_true, y_pred), 3)
    prec_score = round(precision_score(y_true, y_pred), 3)
    rec_score = round(recall_score(y_true, y_pred), 3)
    
    metrics["fpr"] = [round(f, 3) for f in fpr_list]
    metrics["tpr"] = [round(f, 3) for f in tpr_list]
    metrics["thrs"] = [round(f, 3) for f in thr_list]
    metrics["confusion_matrix"] = c_matrix.tolist()
    metrics["avg_precision_score"] = avg_precision_score
    metrics["f1_score"] = f1
    metrics["log_loss"] = lg_loss
    metrics["precision_score"] = prec_score
    metrics["recall_score"] = rec_score
    
    return metrics
