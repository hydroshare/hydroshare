import json
import os
import redpanda_connect
import logging
import asyncio

from hsextract.hs_cn_schemas.schema.src.base import HasPart
from hsextract.utils.models import ContentType, MetadataObject
from hsextract.utils.s3 import write_metadata, load_metadata, delete_metadata


def determine_required_for_content_type(file_object_path: str, content_type: ContentType) -> bool:
    # For fileset and single file, it only matters if it is the
    # hs_user_meta.json file
    return True


def write_resource_metadata(md: MetadataObject) -> bool:
    # read the system metadata file
    system_json = load_metadata(md.system_metadata_path)

    # read the resource metadata hs_user_meta.json file
    user_json = load_metadata(md.user_metadata_path)

    # generate content type hasPart relationships
    # content_type_metadata_paths: list[str] = [file for file in find(md.resource_md_path)
    # if file != f"{md.resource_md_path}/dataset_metadata.json"]
    content_type_metadata_paths = []
    has_parts = []
    for file in content_type_metadata_paths:
        content_type_metadata = load_metadata(file)

        # Remove the bucket name from the path
        file_prefix = '/'.join(file.split('/')[1:])
        has_part = HasPart(  # TODO: probably need content type here as well for driving the landing page
            name=content_type_metadata.get(
                "name", "Not Found and name is required"),
            description=content_type_metadata.get("description", None),
            url=f"{os.environ['AWS_S3_ENDPOINT']}/{file_prefix}",
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
    part_json = {}
    if md.content_type_md_path:
        part_json = load_metadata(md.content_type_md_path)

    # read the content type user metadata file
    user_json = {}
    if md.content_type_md_user_path:
        user_json = load_metadata(md.content_type_md_user_path)

    # generate content type isPartOf relationships
    resource_md_prefix = '/'.join(md.resource_md_path.split('/')[1:])
    # TODO: determine whether to use IsPartOf
    is_part_of = [f"{os.environ['AWS_S3_ENDPOINT']}/{resource_md_prefix}"]

    content_type_associated_media = md.content_type_associated_media()

    # Combine part metadata, user metadata, isPartOf, and associatedMedia
    # TODO evaluate whether we need to merge list properties
    combined_metadata = {**part_json, **user_json}
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
            md.extract_metadata()
            write_content_type_metadata(md)
        else:
            delete_metadata(md.content_type_md_path)

    logging.info("Writing resource metadata")
    write_resource_metadata(md)


@redpanda_connect.processor
def handle_minio_event(msg: redpanda_connect.Message) -> redpanda_connect.Message:
    json_payload = json.loads(msg.payload)
    if ".hsjsonld" in json_payload['Key']:
        return msg
    workflow_metadata_extraction(json_payload['Key'], json_payload[
                                 'EventName'].startswith("s3:ObjectCreated"))


if __name__ == "__main__":
    asyncio.run(redpanda_connect.processor_main(handle_minio_event))
