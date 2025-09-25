import json
import os
import redpanda_connect
import logging
import asyncio

from hs_cloudnative_schemas.schema.base import HasPart
from hsextract.utils.models import ContentType, MetadataObject
from hsextract.utils.s3 import find, write_metadata, load_metadata, delete_metadata


def write_resource_metadata(md: MetadataObject) -> bool:
    # read the system metadata file
    system_json = load_metadata(md.system_metadata_path)

    # read the resource metadata hs_user_meta.json file
    user_json = load_metadata(md.user_metadata_path)

    # generate content type hasPart relationships
    content_type_metadata_paths: list[str] = [file for file in find(md.resource_md_jsonld_path)
                                              if file != f"{md.resource_md_jsonld_path}/dataset_metadata.json"]
    has_parts = []
    for file in content_type_metadata_paths:
        content_type_metadata = load_metadata(file)

        # Remove the bucket name from the path
        has_part = HasPart(  # TODO: probably need content type here as well for driving the landing page
            name=content_type_metadata.get("name", None),
            description=content_type_metadata.get("description", None),
            url=f"{os.environ['AWS_S3_ENDPOINT']}/{file}",
        )
        has_parts.append(has_part.model_dump(exclude_none=True))

    # Combine system metadata, user metadata, hasPart, and associatedMedia
    # TODO evaluate whether we need to merge list properties
    combined_metadata = {**system_json, **user_json}
    combined_metadata["hasPart"] = has_parts
    combined_metadata["associatedMedia"] = md.resource_associated_media

    # Write the combined metadata to the resource metadata file
    write_metadata(md.resource_metadata_path, combined_metadata)


def write_content_type_metadata(md: MetadataObject) -> bool:
    # read the part metadata file
    logging.info(f"Reading content type metadata from {md.content_type_md_path}")
    content_type_metadata = load_metadata(md.content_type_md_path)

    # read the content type user metadata file
    logging.info(f"Reading content type user metadata from {
                 md.content_type_md_user_path}")
    user_json = load_metadata(md.content_type_md_user_path)
    logging.info(f"Read content type user metadata: {user_json}")

    # generate content type isPartOf relationships
    is_part_of = [f"{os.environ['AWS_S3_ENDPOINT']}/{md.resource_md_jsonld_path}/dataset_metadata.json"]

    content_type_associated_media = md.content_type_associated_media()

    # Combine part metadata, user metadata, isPartOf, and associatedMedia
    # TODO evaluate whether we need to merge list properties
    combined_metadata = {**content_type_metadata, **user_json}
    combined_metadata["isPartOf"] = is_part_of
    combined_metadata["associatedMedia"] = content_type_associated_media

    # Write the combined metadata to the resource metadata file
    write_metadata(md.content_type_md_jsonld_path, combined_metadata)


# if a file is not updated, it is deleted
def workflow_metadata_extraction(file_object_path: str, file_updated: bool = True) -> None:
    md = MetadataObject(file_object_path, file_updated)
    logging.info(f"content type determined: {md.content_type}")
    # fileset and single file do not have anything to extract
    if md.content_type != ContentType.UNKNOWN:
        if file_updated:
            logging.info(f"Extracting metadata for {md.file_object_path}")
            md.extract_metadata()
            logging.info(f"Extracted metadata for {md.file_object_path}")
            write_content_type_metadata(md)
        else:
            delete_metadata(md.content_type_md_path)
    write_resource_metadata(md)


@redpanda_connect.processor
def handle_minio_event(msg: redpanda_connect.Message) -> redpanda_connect.Message:
    json_payload = json.loads(msg.payload)
    key = json_payload['Key']
    directory = key.split('/')[2]
    logging.info(f"Received event for key: {key}, directory: {directory}")
    # 0 is bucket
    # 1 is resource id
    if directory == ".hsjsonld":
        return
    if directory == ".hsmetadata":
        logging.info("Event in .hsmetadata directory")
        if key.endswith("system_metadata.json"):
            logging.info("System metadata change, updating resource metadata")
            # TODO create resource metadata
        elif key.endswith("user_metadata.json"):
            logging.info("User metadata change, updating content type metadata")
            # TODO determine if content type user metadata to create content
            # type metadata or resource metadata
        else:
            logging.info(f"No event for all other files in .hsmetadata (they are metadata extracted from content types): {key}")
        return
    workflow_metadata_extraction(
        key, json_payload['EventName'].startswith("s3:ObjectCreated"))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(redpanda_connect.processor_main(handle_minio_event))
