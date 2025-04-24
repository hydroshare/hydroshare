import enum


class AggregationMetaFilePath(str, enum.Enum):
    RESMAP_FILE_ENDSWITH = "_resmap.xml"
    METADATA_FILE_ENDSWITH = "_meta.xml"
    SCHEMA_JSON_FILE_ENDSWITH = "_schema.json"
    METADATA_JSON_FILE_NAME = "hs_user_metadata.json"
    METADATA_JSON_FILE_ENDSWITH = ".hs_user_metadata.json"
