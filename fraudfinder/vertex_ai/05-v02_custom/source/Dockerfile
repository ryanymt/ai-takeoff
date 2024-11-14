FROM python:3.10

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN apt-get install -y apt-transport-https ca-certificates 

# Add the repository for gnupg
#RUN add-apt-repository -y ppa:gnupg-maint/ppa

RUN apt-get update
#RUN apt-get install -y gnupg

RUN echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | tee -a /etc/apt/sources.list.d/google-cloud-sdk.list 
RUN curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | gpg --dearmor -o /usr/share/keyrings/cloud.google.gpg 
RUN apt-get update

RUN apt-get install -y google-cloud-cli
# Set the PATH to include gcloud CLI
#ENV PATH="/google-cloud-sdk/bin:$PATH"

# Initialize gcloud CLI
#RUN gcloud init --console-only

RUN curl -v https://storage.googleapis.com/fraud123-438914-fraudfinder/config/notebook_env_02.py


CMD ["python", "main.py"]
