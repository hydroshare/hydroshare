import json
import os
import redpanda_connect
import logging
import asyncio
from hs_cloudnative_schemas.schema.base import HasPart
from hsextract.content_types.models import ContentType, ResourceUserMetadataObject, SystemMetadataObject
from hsextract.content_types import determine_content_type_from_user_metadata, determine_metadata_object, BaseMetadataObject
from hsextract.utils.s3 import find, write_metadata, load_metadata, delete_metadata


def write_resource_jsonld_metadata(md: BaseMetadataObject) -> bool:
    # read the system metadata file
    system_json = load_metadata(md.system_metadata_path)
    print(f"System metadata loaded: {system_json} from {md.system_metadata_path}")

    # read the user resource metadata file
    user_json = load_metadata(md.user_metadata_path)
    print(f"User metadata loaded: {user_json} from {md.user_metadata_path}")

    # generate content type hasPart relationships
    print(f"Finding content type metadata files in {md.resource_md_jsonld_path}")
    content_type_metadata_paths: list[str] = [file for file in find(md.resource_md_jsonld_path)
                                              if file != f"{md.resource_md_jsonld_path}/dataset_metadata.json"]
    print(f"Content type metadata paths found: {content_type_metadata_paths}")
    has_parts = []
    for file in content_type_metadata_paths:
        content_type_metadata = load_metadata(file)

        has_part = HasPart(  # TODO: probably need content type here as well for driving the landing page
            name=content_type_metadata.get("name", None),
            description=content_type_metadata.get("description", None),
            url=f"{os.environ['AWS_S3_ENDPOINT_URL']}/{file}",
        )
        has_parts.append(has_part.model_dump(exclude_none=True))
    print(f"Generated hasPart relationships: {has_parts}")
    # Combine system metadata, user metadata, hasPart, and associatedMedia
    # TODO evaluate whether we need to merge list properties
    combined_metadata = {**system_json, **user_json}
    print(f"Combined system and user metadata: {combined_metadata}")
    combined_metadata["hasPart"] = has_parts
    print(f"Added hasPart to combined metadata: {combined_metadata}")
    combined_metadata["associatedMedia"] = md.resource_associated_media
    print(f"Combined resource metadata: {combined_metadata}")

    # Write the combined metadata to the resource metadata file
    write_metadata(md.resource_metadata_jsonld_path, combined_metadata)


def write_content_type_jsonld_metadata(md: BaseMetadataObject) -> bool:
    # read the part metadata file
    print(f"Reading content type metadata from {md.content_type_md_path}")
    content_type_metadata = load_metadata(md.content_type_md_path)

    # read the content type user metadata file
    print(f"Reading content type user metadata from {md.content_type_md_user_path}")
    user_json = load_metadata(md.content_type_md_user_path)
    print(f"Read content type user metadata: {user_json} for {md.content_type_md_user_path}")
    if not content_type_metadata and not user_json:
        print(f"No content type or user metadata to write for {md.content_type_md_jsonld_path}")
        return
    # generate content type isPartOf relationships
    is_part_of = [f"{os.environ['AWS_S3_ENDPOINT_URL']}/{md.resource_md_jsonld_path}/dataset_metadata.json"]

    content_type_associated_media = md.content_type_associated_media()
    print(f"Content type associated media: {content_type_associated_media}")

    # Combine part metadata, user metadata, isPartOf, and associatedMedia
    # TODO evaluate whether we need to merge list properties
    combined_metadata = {**content_type_metadata, **user_json}
    combined_metadata["isPartOf"] = is_part_of
    # TODO make associated media determination consistent with all content types
    combined_metadata["associatedMedia"] = combined_metadata.get("associatedMedia", []) + content_type_associated_media

    # Write the combined metadata to the content type metadata file
    write_metadata(md.content_type_md_jsonld_path, combined_metadata)


# if a file is not updated, it is deleted
def workflow_metadata_extraction(file_object_path: str, file_updated: bool = True) -> None:
    md = determine_metadata_object(file_object_path, file_updated)
    print(f"wooo wooo content type determined: {md.content_type}")
    # fileset and single file do not have anything to extract
    if md.content_type != ContentType.UNKNOWN:
        if file_updated:
            print(f"Extracting metadata for {md.file_object_path}")
            content_type_metadata = md.extract_metadata()
            if content_type_metadata:
                write_metadata(md.content_type_md_path, content_type_metadata)
            print(f"Extracted metadata for {md.file_object_path}")
            write_content_type_jsonld_metadata(md)
            files_to_cleanup = md.clean_up_extracted_metadata()
            for f in files_to_cleanup:
                print(f"Cleaning up extracted metadata file {f}")
                delete_metadata(f)
        else:
            # TODO: not all file deletes for content types will need metadata deleted but rather updated
            print(f"Deleting metadata for {md.file_object_path}")
            delete_metadata(md.content_type_md_path)
            delete_metadata(md.content_type_md_jsonld_path)
    print(f"Writing resource metadata for {md.resource_md_jsonld_path}")
    write_resource_jsonld_metadata(md)


@redpanda_connect.processor
def handle_minio_event(msg: redpanda_connect.Message) -> redpanda_connect.Message:
    json_payload = json.loads(msg.payload)
    key = json_payload['Key']
    file_updated = json_payload['EventName'].startswith("s3:ObjectCreated")
    directory = key.split('/')[2]
    bucket = key.split('/')[0]
    resource_id = key.split('/')[1]
    print(f"Received event for key: {key}, directory: {directory}")
    if directory == ".hsjsonld":
        return
    if directory == ".hsmetadata":
        print("Event in .hsmetadata directory " + key)
        if key == f"{bucket}/{resource_id}/.hsmetadata/user_metadata.json":
            md = BaseMetadataObject(key, file_updated)
            write_resource_jsonld_metadata(md)
        elif key == f"{bucket}/{resource_id}/.hsmetadata/system_metadata.json":
            print("System metadata change, updating resource metadata")
            md = BaseMetadataObject(key, file_updated)
            write_resource_jsonld_metadata(md)
        elif key.endswith("user_metadata.json"):
            # folder type, just find a file in the folder to determine content type
            md = determine_content_type_from_user_metadata(key, file_updated)
            write_content_type_jsonld_metadata(md)
        else:
            print(f"No event for all other files in .hsmetadata: {key}")
        return
    workflow_metadata_extraction(key, file_updated)


def resource_level(path: str) -> bool:
    parts = path.split('/')
    return len(parts) == 3 or (len(parts) == 4 and parts[3] == '')


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(redpanda_connect.processor_main(handle_minio_event))
