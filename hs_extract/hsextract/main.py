import logging
import json
import os
import redpanda_connect
import asyncio
from hs_cloudnative_schemas.schema.base import HasPart
from hsextract.content_types.models import ContentType
from hsextract.content_types import determine_metadata_object, BaseMetadataObject
from hsextract.utils.s3 import find, write_metadata, load_metadata, delete_metadata


def _normalize_list(value) -> list:
    if not value:
        return []
    if isinstance(value, list):
        return value
    return [value]



def write_resource_jsonld_metadata(md: BaseMetadataObject) -> bool:
    # read the system metadata file
    system_json = load_metadata(md.system_metadata_path)

    # read the user resource metadata file
    user_json = load_metadata(md.user_metadata_path)

    # generate content type hasPart relationships
    content_type_metadata_paths: list[str] = [file for file in find(md.resource_md_jsonld_path)
                                              if file != f"{md.resource_md_jsonld_path}/dataset_metadata.json"]
    has_parts = []
    for file in content_type_metadata_paths:
        content_type_metadata = load_metadata(file)

        has_part = HasPart(  # TODO: probably need content type here as well for driving the landing page
            name=content_type_metadata.get("name", None),
            description=content_type_metadata.get("description", None),
            url=f"{os.environ['AWS_S3_ENDPOINT_URL']}/{file}",
        )
        has_parts.append(has_part.model_dump(exclude_none=True))

    # Combine system metadata, user metadata, hasPart, and associatedMedia (join arrays)
    combined_metadata = {**system_json, **user_json}
    combined_metadata["hasPart"] = (
        has_parts
        + _normalize_list(system_json.get("hasPart"))
        + _normalize_list(user_json.get("hasPart"))
    )
    combined_metadata["associatedMedia"] = md.resource_associated_media

    # Write the combined metadata to the resource metadata file
    write_metadata(md.resource_metadata_jsonld_path, combined_metadata)


def write_content_type_jsonld_metadata(md: BaseMetadataObject) -> bool:
    # read the part metadata file
    content_type_metadata = load_metadata(md.content_type_md_path)

    # read the content type user metadata file
    user_json = load_metadata(md.content_type_md_user_path)
    if not content_type_metadata and not user_json:
        return
    # generate content type isPartOf relationships
    is_part_of = [f"{os.environ['AWS_S3_ENDPOINT_URL']}/{md.resource_md_jsonld_path}/dataset_metadata.json"]

    content_type_associated_media = md.content_type_associated_media()

    # Combine part metadata, user metadata, isPartOf, and associatedMedia (join arrays)
    combined_metadata = {**content_type_metadata, **user_json}
    combined_metadata["hasPart"] = (
        _normalize_list(content_type_metadata.get("hasPart"))
        + _normalize_list(user_json.get("hasPart"))
    )
    combined_metadata["isPartOf"] = _normalize_list(content_type_metadata.get("isPartOf")) + is_part_of
    # TODO make associated media determination consistent with all content types
    combined_metadata["associatedMedia"] = combined_metadata.get("associatedMedia", []) + content_type_associated_media

    # Write the combined metadata to the content type metadata file
    write_metadata(md.content_type_md_jsonld_path, combined_metadata)


# if a file is not updated, it is deleted
def workflow_metadata_extraction(file_object_path: str, file_updated: bool = True) -> None:
    md = determine_metadata_object(file_object_path, file_updated)
    # fileset and single file do not have anything to extract
    if md.content_type != ContentType.UNKNOWN:
        if file_updated:
            content_type_metadata = md.extract_metadata()
            if content_type_metadata:
                write_metadata(md.content_type_md_path, content_type_metadata)
            write_content_type_jsonld_metadata(md)
            files_to_cleanup = md.clean_up_extracted_metadata()
            for f in files_to_cleanup:
                delete_metadata(f)
        else:
            # TODO: not all file deletes for content types will need metadata deleted but rather updated
            delete_metadata(md.content_type_md_path)
            delete_metadata(md.content_type_md_jsonld_path)
    write_resource_jsonld_metadata(md)


@redpanda_connect.processor
def handle_minio_event(msg: redpanda_connect.Message) -> redpanda_connect.Message:
    print(f"Received message: {msg.payload}")
    json_payload = json.loads(msg.payload)
    key = json_payload['Key']
    file_updated = json_payload['EventName'].startswith("s3:ObjectCreated")
    directory = key.split('/')[2]
    bucket = key.split('/')[0]
    resource_id = key.split('/')[1]
    if directory == ".hsjsonld":
        return
    elif directory == ".hsmetadata":
        print(f"Handling .hsmetadata event for file: {key}, updated: {file_updated}")
        if key == f"{bucket}/{resource_id}/.hsmetadata/user_metadata.json":
            md = BaseMetadataObject(key, file_updated)
            write_resource_jsonld_metadata(md)
        elif key == f"{bucket}/{resource_id}/.hsmetadata/system_metadata.json":
            md = BaseMetadataObject(key, file_updated)
            write_resource_jsonld_metadata(md)
        elif key.endswith("user_metadata.json"):
            print(f"User metadata event for content types in .hsmetadata not currently implemented: {key}")
        else:
            print(f"No event for all other files in .hsmetadata: {key}")
        return
    else:
        workflow_metadata_extraction(key, file_updated)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(redpanda_connect.processor_main(handle_minio_event))
