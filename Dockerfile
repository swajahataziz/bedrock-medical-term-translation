FROM public.ecr.aws/docker/library/python:3.11-slim
 
EXPOSE 8083
WORKDIR /app
RUN apt-get update && apt-get install -y \
build-essential \
software-properties-common \
git \
curl \
unzip \
wget \
&& rm -rf /var/lib/apt/lists/*
COPY .aws_creds /root/.aws/credentials
RUN git clone https://github.com/swajahataziz/bedrock-medical-term-translation.git /app/bedrockcode
RUN cd /app/bedrockcode/
WORKDIR /app/bedrockcode/
#ARG AWS_REGION="us-east-1"
#ARG KENDRA_INDEX_ID="4c9f674c-2b78-43a2-a6a3-6f4157c23967"
#ARG AWS_PROFILE=default
ENV AWS_REGION=us-east-1
ENV KENDRA_INDEX_ID=4c9f674c-2b78-43a2-a6a3-6f4157c23967
ENV AWS_PROFILE=default
RUN pip install -r requirements.txt
RUN wget https://d2eo22ngex1n9g.cloudfront.net/Documentation/SDK/bedrock-python-sdk.zip
RUN unzip bedrock-python-sdk.zip
RUN ls
RUN pip install --no-build-isolation --force-reinstall \
awscli-1.29.21-py3-none-any.whl \
boto3-1.28.21-py3-none-any.whl \
botocore-1.31.21-py3-none-any.whl
ENTRYPOINT ["streamlit", "run", "/app/bedrockcode/app.py","bedrock_titan", "--server.port=8083", "--server.address=0.0.0.0"]
