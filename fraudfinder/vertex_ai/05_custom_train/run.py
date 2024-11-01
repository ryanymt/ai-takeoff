import yaml
from google.cloud import aiplatform as vertex_ai


with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

dataset = vertex_ai.TabularDataset(
    f"projects/{config['PROJECT']}/location/{config['REGION']}/datasets/{config['DATASET_ID']}"
)
job = vertex_ai.CustomContainerTrainingJob(
    display_name=f"fraudfinder_xgb_train_frmlz-{config['ID']}",
    container_uri=config["IMAGE_URI"],
    model_serving_container_image_uri=config["MODEL_SERVING_IMAGE_URI"],
)

model = job.run(
    dataset=dataset,
    model_display_name=config["MODEL_NAME"],
    replica_count=1,
    persistent_resource_id=config["RESOURCE_ID"],
)