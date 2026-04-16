import os
from django.db import connection
from .settings import get_default_zone_config, get_zone_config, get_default_zone_name


def bucket_and_zone(path):
    if path.startswith("bags/") or path.startswith("tmp/") or path.startswith("zips/"):
        zone_config = get_default_zone_config()
        return zone_config.bucket_name, get_default_zone_name()
    res_id = path.split("/")[0] if "/" in path else path
    resource_query = 'SELECT quota_holder_id \
                        FROM hs_core_genericresource \
                        WHERE short_id = %s'

    with connection.cursor() as cursor:
        cursor.execute(resource_query, [res_id])
        row = cursor.fetchone()
        if row is None:
            raise Exception(f"Resource with short_id {res_id} not found")
        owner_id = row[0]
    with connection.cursor() as cursor:
        zone_userquota_query = 'SELECT zone FROM theme_userquota WHERE user_id = %s'
        cursor.execute(zone_userquota_query, [owner_id])
        row = cursor.fetchone()
        zone = row[0]

    zone_config = get_zone_config(zone)
    bucket_name = zone_config.bucket_name
    return bucket_name, zone


def is_metadata_xml_file(file_path):
    """Determine whether a given file is metadata.
    Note: this will return true for any file that ends with the metadata endings
    We are taking the risk that user might create a file with the same filename ending
    """
    from hs_file_types.enums import AggregationMetaFilePath

    if not (file_path.endswith(AggregationMetaFilePath.METADATA_FILE_ENDSWITH.value)
            or file_path.endswith(AggregationMetaFilePath.RESMAP_FILE_ENDSWITH.value)):
        return False
    return True


def is_metadata_json_file(file_path):
    """Determine whether a given file is a metadata json file.
    Note: this will return true for any file that ends with the metadata endings or
    has the same name as the metadata json file
    """
    from hs_file_types.enums import AggregationMetaFilePath

    if file_path.endswith(AggregationMetaFilePath.METADATA_JSON_FILE_ENDSWITH.value):
        return True

    file_name = os.path.basename(file_path)
    return file_name == AggregationMetaFilePath.METADATA_JSON_FILE_NAME.value


def is_schema_json_file(file_path):
    """Determine whether a given file is a schema.json file.
    Note: this will return true for any file that ends with the _schema.json ending
    We are taking the risk that user might create a file with the same filename ending
    """
    from hs_file_types.enums import AggregationMetaFilePath

    return file_path.endswith(AggregationMetaFilePath.SCHEMA_JSON_FILE_ENDSWITH.value)


def is_schema_json_values_file(file_path):
    """Determine whether a given file is a schema_values.json file.
    Note: this will return true for any file that ends with the _schema_values.json ending
    We are taking the risk that user might create a file with the same filename ending
    """
    from hs_file_types.enums import AggregationMetaFilePath

    return file_path.endswith(AggregationMetaFilePath.SCHEAMA_JSON_VALUES_FILE_ENDSWITH.value)
