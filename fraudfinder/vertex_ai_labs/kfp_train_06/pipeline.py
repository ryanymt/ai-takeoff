from kfp import dsl
from google_cloud_pipeline_components.v1 import dataset, custom_job, endpoint

from fraudfinder.vertex_ai_labs.kfp_train_06 import vertex_config
from fraudfinder.vertex_ai_labs.kfp_train_06.ingest_gcs_feature.component import ingest_features_gcs
from fraudfinder.vertex_ai_labs.kfp_train_06.custom_train.component import train_model
from fraudfinder.vertex_ai_labs.kfp_train_06.custom_eval.component import evaluate_model


@dsl.pipeline(
    pipeline_root=vertex_config.PIPELINE_ROOT,
    name=vertex_config.PIPELINE_NAME,
)
def pipeline(
    project_id: str = vertex_config.PROJECT_ID,
    region: str = vertex_config.REGION,
    bucket_name: str = f"gs://{vertex_config.BUCKET_NAME}",
    feature_store_id: str = vertex_config.FEATURESTORE_ID,
    read_instances_uri: str = vertex_config.READ_INSTANCES_URI,
    deploy_machine_type: str = vertex_config.DEPLOY_COMPUTE,
    metrics_uri: str = vertex_config.METRICS_URI,
    model_threshold: float = vertex_config.MODEL_THRESHOLD,
    thold: float = vertex_config.AVG_PR_THRESHOLD,
):
    # Ingest data from featurestore
    ingest_features_op = ingest_features_gcs(
        project_id=project_id,
        region=region,
        bucket_name=bucket_name,
        feature_store_id=feature_store_id,
        read_instances_uri=read_instances_uri,
    )

    # create dataset
    dataset_create_op = dataset.TabularDatasetCreateOp(
        display_name=vertex_config.DATASET_NAME,
        project=project_id,
        gcs_source=ingest_features_op.output,
    ).after(ingest_features_op)

    # custom training job component - script
    train_model_component = custom_job.create_custom_training_job_from_component(
        train_model,
        display_name=vertex_config.JOB_NAME,
        replica_count=vertex_config.REPLICA_COUNT,
        machine_type=vertex_config.TRAIN_COMPUTE,
        base_output_directory=f"gs://{vertex_config.BUCKET_NAME}",
        # persistent_resource_id=PERSISTENT_RESOURCE_ID,
    )
    train_model_op = train_model_component(
        project=project_id,
        dataset=dataset_create_op.outputs["dataset"],
        bucket=f"gs://{vertex_config.BUCKET_NAME}",
    ).after(dataset_create_op)

    # evaluate component
    evaluate_model_op = evaluate_model(
        threshold=model_threshold,
        model_in=train_model_op.outputs["trained_model"], 
        test_ds=train_model_op.outputs["test_ds"],
        metrics_uri=metrics_uri,
    ).after(train_model_op)

    # if threshold on avg_precision_score
    with dsl.If(
        evaluate_model_op.outputs["avg_prec"] > thold, name=vertex_config.AVG_PR_CONDITION
    ):
        # create endpoint
        create_endpoint_op = endpoint.EndpointCreateOp(
            display_name=f"{vertex_config.ENDPOINT_NAME}_xgb_pipeline_{vertex_config.ID}",
            project=project_id,
            location=vertex_config.REGION,
        ).after(evaluate_model_op)

        # deploy the model
        custom_model_deploy_op = endpoint.ModelDeployOp(
            model=train_model_op.outputs["trained_model"],
            endpoint=create_endpoint_op.outputs["endpoint"],
            deployed_model_display_name=f"{vertex_config.MODEL_NAME}_xgb_pipeline_{vertex_config.ID}",
            dedicated_resources_machine_type=deploy_machine_type,
            dedicated_resources_min_replica_count=vertex_config.REPLICA_COUNT,
        ).after(create_endpoint_op)
