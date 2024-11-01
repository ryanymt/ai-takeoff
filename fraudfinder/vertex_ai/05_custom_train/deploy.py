import yaml
import argparse
from google.cloud import aiplatform as vertex_ai


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-m", "--model", required=True)
    args = parser.parse_args()

    with open("config.yaml", "r") as f:
        config = yaml.safe_load(f)

    vertex_ai.init(
        project=config['PROJECT'],
        location=config['REGION'],
        staging_bucket=config['BUCKET_NAME'],
        experiment=f"fraudfinder-xgb-experiment-{config['ID']}",
    )

    # Percentage of traffic that the model will receive in the endpoint
    TRAFFIC_SPLIT = {"0": 100}

    # Parameters to configure the minimum and maximum nodes during autoscaling
    MIN_NODES = 1
    MAX_NODES = 1

    model = vertex_ai.Model(f"projects/{config['PROJECT']}/locations/{config['REGION']}/models/{args.model}")

    endpoint = model.deploy(
        deployed_model_display_name=f"{config['MODEL_NAME']}_xgb_frmlz_{config['ID']}",
        traffic_split=TRAFFIC_SPLIT,
        machine_type=config["DEPLOY_COMPUTE"],
        accelerator_count=0,
        min_replica_count=MIN_NODES,
        max_replica_count=MAX_NODES,
    )
