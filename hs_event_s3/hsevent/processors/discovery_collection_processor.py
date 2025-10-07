import asyncio
import datetime
import logging
import re
import redpanda_connect
import json

import boto3
from pymongo import MongoClient
import os


s3 = boto3.client('s3')

mongo_connection_url = os.getenv("MONGO_CONNECTION_URL", None)
hydroshare_atlas_db = None
if mongo_connection_url:
    hydroshare_atlas_db = MongoClient(mongo_connection_url)["hydroshare"]

datetime_format_regex = re.compile(r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{6}\+\d{2}:\d{2}$')
datetime_format = "%Y-%m-%d %H:%M:%S.%f%z"


def datetime_parser(dct):
    for k, v in dct.items():
        if isinstance(v, str) and datetime_format_regex.match(v):
            dct[k] = datetime.strptime(v, datetime_format)
    return dct


def collect_file_to_catalog(filepath: str):
    bucket_name, object_key = filepath.split('/', 1)
    response = s3.get_object(Bucket=bucket_name, Key=object_key)
    metadata_json = json.loads(response['Body'].read(), object_hook=datetime_parser)
    metadata_json['_s3_filepath'] = filepath
    metadata_json['first_creator'] = (
        metadata_json['creator'][0]
        if 'creator' in metadata_json and metadata_json['creator']
        else None
    )
    content_types = []
    if "hasPart" in metadata_json:
        for part in metadata_json['hasPart']:
            content_type_metadata = hydroshare_atlas_db["discovery"].find_one({"url": part["url"]})
            content_types.append(content_type_metadata["additionalType"])
        metadata_json['content_types'] = list(set(content_types))

    typeahead_json = {}
    typeahead_json['name'] = metadata_json['name']
    typeahead_json['description'] = metadata_json['description']
    typeahead_json['keywords'] = metadata_json['keywords']
    typeahead_json['url'] = metadata_json['url']
    typeahead_json['_s3_filepath'] = filepath


    hydroshare_atlas_db["discovery"].find_one_and_replace({"_s3_filepath": metadata_json["_s3_filepath"]},
                                                          metadata_json, upsert=True)
    hydroshare_atlas_db["typeahead"].find_one_and_replace({"_s3_filepath": metadata_json["_s3_filepath"]},
                                                          metadata_json, upsert=True)


def delete_file_from_catalog(filepath: str):
    try:
        s3.head_object(Bucket=filepath.split('/')[0], Key='/'.join(filepath.split('/')[1:]))
    except s3.exceptions.ClientError as e:
        if e.response['Error']['Code'] == "404":
            hydroshare_atlas_db["discovery"].delete_one({"_s3_filepath": filepath})
            hydroshare_atlas_db["typeahead"].delete_one({"_s3_filepath": filepath})


@redpanda_connect.processor
def discovery_collection_event(msg: redpanda_connect.Message) -> redpanda_connect.Message:
    if hydroshare_atlas_db is None:
        logging.info("Skipping discovery collection event processing since MONGO_CONNECTION_URL is not set")
        return
    logging.info("Received message from Redpanda discovery collection event")
    json_payload = json.loads(msg.payload)
    key = json_payload['Key']
    file_created = json_payload['EventName'].startswith("s3:ObjectCreated")
    bucket_name = key.split('/')[0]
    resource_id = key.split('/')[1]
    if key.startswith(f'{bucket_name}/{resource_id}/.hsjsonld/'):
        logging.info(f"Processing discovery collection event for file {key}")
        if file_created:
            collect_file_to_catalog(key)
        else:
            delete_file_from_catalog(key)
    else:
        logging.info(f"Skipping discovery collection event for file {key} since it is not in "
                     f"{bucket_name}/{resource_id}/.hsjsonld/ folder")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(redpanda_connect.processor_main(discovery_collection_event))
