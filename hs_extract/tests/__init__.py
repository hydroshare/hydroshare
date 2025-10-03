import json
import os
import boto3


s3_config = {
    "endpoint_url": os.environ.get("AWS_S3_ENDPOINT", "https://s3.beta.hydroshare.org"),
    "aws_access_key_id": os.environ.get("AWS_ACCESS_KEY_ID", "YOUR_ACCESS_KEY"),
    "aws_secret_access_key": os.environ.get("AWS_SECRET_ACCESS_KEY", "YOUR_SECRET_KEY")
}
s3_client = boto3.client('s3', **s3_config)


def read_s3_json(path: str):
    bucket, key = path.split("/", 1)
    response = s3_client.get_object(
        Bucket=bucket,
        Key=key
    )
    file_content = response['Body'].read().decode('utf-8')
    metadata_json = json.loads(file_content)
    return metadata_json


def write_s3_json(path: str, metadata_json: dict):
    bucket, key = path.split("/", 1)
    s3_client.put_object(
        Bucket=bucket,
        Key=key,
        Body=json.dumps(metadata_json, indent=2).encode('utf-8'),
        ContentType='application/json'
    )
