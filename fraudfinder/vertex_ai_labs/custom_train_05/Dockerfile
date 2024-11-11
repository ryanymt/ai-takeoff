# Specifies base image and tag
FROM python:3.10
WORKDIR /root

# Installs additional packages
RUN pip install gcsfs pyyaml numpy pandas scikit-learn dask distributed xgboost requests pydantic --upgrade

# Copies the trainer code to the docker image.
COPY . ./

# Sets up the entry point to invoke the trainer.
ENTRYPOINT ["python3", "-m", "trainer.task"]