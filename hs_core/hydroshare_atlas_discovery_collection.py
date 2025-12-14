import datetime
import re
import json

import boto3
from pymongo import MongoClient
from django.conf import settings
from urllib.parse import urlparse


s3 = boto3.client('s3')

mongo_connection_url = settings.ATLAS_CONNECTION_URL
hydroshare_atlas_db = MongoClient(mongo_connection_url)["hydroshare"]

datetime_format_regex = re.compile(r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{6}\+\d{2}:\d{2}$')
temporal_coverage_datetime_format_regex = re.compile(r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$')
datetime_format = "%Y-%m-%d %H:%M:%S.%f%z"
temporal_coverage_datetime_format = "%Y-%m-%d %H:%M:%S"


def datetime_parser(dct):
    for k, v in dct.items():
        if isinstance(v, str):
            if datetime_format_regex.match(v):
                dct[k] = datetime.datetime.strptime(v, datetime_format)
            if temporal_coverage_datetime_format_regex.match(v):
                dct[k] = datetime.datetime.strptime(v, temporal_coverage_datetime_format)
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
            part_key = '/'.join(urlparse(part['url']).path.split('/')[2:])
            s3_response = s3.get_object(Bucket=bucket_name, Key=part_key)
            s3_object_body = s3_response.get('Body')
            content = s3_object_body.read()
            json_dict = json.loads(content)
            content_types.append(json_dict.get('additionalType'))
        metadata_json['content_types'] = list(set(content_types))

    hydroshare_atlas_db["discovery"].find_one_and_replace({"_s3_filepath": metadata_json["_s3_filepath"]},
                                                          metadata_json, upsert=True)


def delete_file_from_catalog(filepath: str):
    print("Deleting file from catalog:", filepath)
    hydroshare_atlas_db["discovery"].delete_one({"_s3_filepath": filepath})
