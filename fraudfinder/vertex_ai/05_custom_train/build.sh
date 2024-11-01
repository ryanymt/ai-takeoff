#/bin/bash
IMAGE_URI="us-central1-docker.pkg.dev/fraud-finder-lab/fraudfinder-8wc8m/dask-xgb-classificator:latest"
IMAGE_REPOSITORY="fraudfinder-8wc8m"

gcloud artifacts repositories create $IMAGE_REPOSITORY --repository-format=docker --location=us-central1 --description="FraudFinder Docker Image repository"
gcloud auth configure-docker us-central1-docker.pkg.dev
docker build ./ -t $IMAGE_URI
docker push $IMAGE_URI