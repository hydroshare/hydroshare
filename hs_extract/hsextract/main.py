import logging
import json
import os
import redpanda_connect
import asyncio
from hs_cloudnative_schemas.schema.base import IsPartOf, HasPart
from hsextract.content_types.models import ContentType
from hsextract.content_types import (
    determine_metadata_object,
    BaseMetadataObject,
    determine_metadata_object_from_user_metadata,
)
from hsextract.utils.s3 import (
    delete_metadata,
    iter_find,
    load_metadata,
    write_file_manifest,
    write_has_part_file,
    write_metadata,
)


def _normalize_list(value) -> list:
    if not value:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _iter_resource_has_parts(md: BaseMetadataObject, user_json: dict):
    jsonld_files_to_exclude = {
        md.resource_metadata_jsonld_path,
        md.resource_associated_media_jsonld_path,
        md.resource_has_parts_jsonld_path,
    }
    for file in iter_find(md.resource_md_jsonld_path):
        if file in jsonld_files_to_exclude:
            continue
        if file.endswith("file_manifest.json"):
            # fileset manifest file - so skip
            continue
        content_type_metadata = load_metadata(file)
        has_part = HasPart(
            name=content_type_metadata.get("name", None),
            description=content_type_metadata.get("description", None),
            url=f"{os.environ['AWS_S3_ENDPOINT_URL']}/{file}",
        )
        yield has_part.model_dump(exclude_none=True)

    for has_part in _normalize_list(user_json.get("hasPart")):
        yield has_part


def write_resource_jsonld_metadata(md: BaseMetadataObject) -> bool:
    # read the system metadata file
    system_json = load_metadata(md.system_metadata_path)

    # read the user resource metadata file
    user_json = load_metadata(md.user_metadata_path)

    # Combine system metadata and user metadata
    combined_metadata = {**system_json, **user_json}

    # TODO: If we can assume that the user is not allowed to edit the hasPart relationship in the user metadata,
    # then we can optimize the generation of the has_parts.json so that we only re-generate this file on
    # specific s3 object notification.
    has_part_reference = write_has_part_file(
        md.resource_has_parts_jsonld_path,
        _iter_resource_has_parts(md, user_json),
    )
    combined_metadata["hasPart"] = [has_part_reference] if has_part_reference else []

    # file_manifest.json is re-generated only on s3 object notification for a data file
    manifest_reference = write_file_manifest(
        md,
        enabled=True
    )
    combined_metadata["associatedMedia"] = [manifest_reference] if manifest_reference else []

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

    # Combine part metadata, user metadata, isPartOf, and associatedMedia (join arrays)
    combined_metadata = {**content_type_metadata, **user_json}
    combined_metadata["hasPart"] = (
        _normalize_list(content_type_metadata.get("hasPart"))
        + _normalize_list(user_json.get("hasPart"))
    )
    combined_metadata["isPartOf"] = _normalize_list(content_type_metadata.get("isPartOf")) + is_part_of
    # create IsPartOf relationship for content type metadata
    is_part_of_models = []
    for jsonld_file_url in combined_metadata.get("isPartOf", []):
        is_part_of_models.append(IsPartOf(
            url=jsonld_file_url
        ).model_dump(exclude_none=True))
    combined_metadata["isPartOf"] = is_part_of_models
    # TODO make associated media determination consistent with all content types
    if md.content_type != ContentType.FILE_SET:
        content_type_associated_media = md.content_type_associated_media()
        combined_metadata["associatedMedia"] = (
            combined_metadata.get("associatedMedia", [])
            + content_type_associated_media
        )
    else:
        # For fileset, a reference to file_manifest.json is used. This is similar to the resource level file manifest.
        # file_manifest.json is re-generated only on s3 object notification for a data file
        manifest_reference = write_file_manifest(
            md,
            enabled=True,
            fileset_manifest=True
        )
        combined_metadata["associatedMedia"] = [manifest_reference] if manifest_reference else []

    # Write the combined metadata to the content type metadata file
    write_metadata(md.content_type_md_jsonld_path, combined_metadata)


# if a file is not updated, it is deleted
def workflow_metadata_extraction(file_object_path: str, file_size: int, file_updated: bool = True) -> None:
    md = determine_metadata_object(file_object_path, file_updated)
    # fileset and single file do not have anything to extract
    if md.content_type != ContentType.UNKNOWN:
        if file_updated:
            if file_size < int(os.environ.get("METADATA_EXTRACTION_FILE_SIZE_LIMIT", 4 * 1024 * 1024 * 1024)):
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

    try:
        write_resource_jsonld_metadata(md)
    except Exception as ex:
        print(f"Error writing resource jsonld metadata: {str(ex)}")


def refresh_resource_metadata(bucket: str, resource_id: str) -> None:
    resource_content_path = f"{bucket}/{resource_id}/data/contents/"
    md = None
    for resource_file in iter_find(resource_content_path):
        md = determine_metadata_object(resource_file, True)
        if md.content_type != ContentType.UNKNOWN:
            try:
                content_type_metadata = md.extract_metadata()
                if content_type_metadata:
                    write_metadata(md.content_type_md_path, content_type_metadata)
                write_content_type_jsonld_metadata(md)
                files_to_cleanup = md.clean_up_extracted_metadata()
                for f in files_to_cleanup:
                    delete_metadata(f)
            except Exception as ex:
                print(f"Error extracting metadata for file {resource_file}: {str(ex)}")
    # TODO determine any metadata files that may need to be deleted
    # if metadata files do not have corresponding data files
    if md:
        write_resource_jsonld_metadata(md)


@redpanda_connect.processor
def handle_minio_event(msg: redpanda_connect.Message) -> redpanda_connect.Message:
    print(f"Received message: {msg.payload}")
    json_payload = json.loads(msg.payload)
    key = json_payload['Key']
    file_updated = json_payload['EventName'].startswith("s3:ObjectCreated")
    file_size = json_payload['Records'][0]['s3']['object']['size']
    directory = key.split('/')[2]
    bucket = key.split('/')[0]
    resource_id = key.split('/')[1]
    if directory == ".hsrefresh":
        refresh_resource_metadata(bucket, resource_id)
        return
    if directory == ".hsjsonld":
        return
    if directory == ".hsmetadata":
        print(f"Handling .hsmetadata event for file: {key}, updated: {file_updated}")
        if key == f"{bucket}/{resource_id}/.hsmetadata/user_metadata.json":
            md = BaseMetadataObject(key, file_updated)
            write_resource_jsonld_metadata(md)
        elif key == f"{bucket}/{resource_id}/.hsmetadata/system_metadata.json":
            md = BaseMetadataObject(key, file_updated)
            write_resource_jsonld_metadata(md)
        elif key.endswith("user_metadata.json"):
            md = determine_metadata_object_from_user_metadata(key, file_updated)
            if md.content_type != ContentType.UNKNOWN:
                write_content_type_jsonld_metadata(md)
                write_resource_jsonld_metadata(md)
        else:
            print(f"No event for all other files in .hsmetadata: {key}")
        return
    else:
        workflow_metadata_extraction(key, file_size, file_updated)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(redpanda_connect.processor_main(handle_minio_event))
