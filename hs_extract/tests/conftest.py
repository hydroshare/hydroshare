import json
import os

from hsextract.utils.s3 import refresh_s3_clients_from_env


os.environ.setdefault(
    "S3_ZONE_CONFIG",
    json.dumps({
        "hydroshare": {
            "bucket_name": "resource",
            "aws_s3_endpoint_url": "http://minio:9000",
            "aws_access_key_id": "cuahsi",
            "aws_secret_access_key": "devpassword",
            "aws_s3_endpoint_url_public": "http://localhost:9000"
        },
        "published": {  # the publisher hydroshare user must be updated to use this zone, see PUBLISHER_USER_NAME
            "bucket_name": "published",
            "aws_s3_endpoint_url": "http://minio:9000",
            "aws_access_key_id": "cuahsi",
            "aws_secret_access_key": "devpassword",
            "aws_s3_endpoint_url_public": "http://localhost:9000"
        },
        "ciroh": {
            "bucket_name": "ciroh",
            "aws_s3_endpoint_url": "http://minio:9000",
            "aws_access_key_id": "cuahsi",
            "aws_secret_access_key": "devpassword",
            "aws_s3_endpoint_url_public": "http://localhost:9000"
        }
    }),
)
os.environ.setdefault("HS_S3_AUTH_EVENT_ENDPOINT", "http://hs-s3-auth/s3/event/")

refresh_s3_clients_from_env()
