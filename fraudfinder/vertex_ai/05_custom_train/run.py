import yaml
import argparse
from google.cloud import aiplatform as vertex_ai


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ps", required=False)
    args = parser.parse_args()

    with open("config.yaml", "r") as f:
        config = yaml.safe_load(f)

    vertex_ai.init(
        project=config['PROJECT'],
        location=config['REGION'],
        staging_bucket=config['BUCKET_NAME'],
        experiment=f"fraudfinder-xgb-experiment-{config['ID']}",
    )

    dataset = vertex_ai.TabularDataset(
        f"projects/{config['PROJECT']}/locations/{config['REGION']}/datasets/{config['DATASET_ID']}"
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
        persistent_resource_id=args.ps,
    )
