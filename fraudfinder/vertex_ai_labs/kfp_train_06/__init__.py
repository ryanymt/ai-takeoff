import yaml
import requests
from fraudfinder.vertex_ai_labs.utils import gcs_read, VertexConfig


# Detect Cloud project from environment
headers = {"Metadata-Flavor": "Google"}
PROJECT_ID = requests.get("http://metadata.google.internal/computeMetadata/v1/project/project-id", headers=headers)
PROJECT_ID = PROJECT_ID.content.decode()
BUCKET_NAME = f"{PROJECT_ID}-fraudfinder"
config_path = "config/vertex_conf.yaml"

with gcs_read(PROJECT_ID, BUCKET_NAME, "config/vertex_conf.yaml").open("r") as f:
    conf = yaml.safe_load(f)
vertex_config = VertexConfig(**conf)
