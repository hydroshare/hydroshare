import os
import logging
from enum import Enum

from hs_cloudnative_schemas.schema.base import MediaObject

from hsextract.utils.s3 import retrieve_file_manifest
from string import Template


resource_contents_path_template = os.environ.get("RESOURCE_CONTENTS_PATH", "$bucket_name/$resource_id/data/contents")
resource_md_jsonld_path_template = os.environ.get("RESOURCE_MD_JSONLD_PATH", "$bucket_name/$resource_id/.hsjsonld")
resource_md_path_template = os.environ.get("RESOURCE_MD_PATH", "$bucket_name/$resource_id/.hsmetadata")


class ContentType(Enum):
    RASTER = "raster"
    NETCDF = "netcdf"
    # ZARR = "zarr"
    FEATURE = "feature"
    TIMESERIES = "timeseries"
    UNKNOWN = "unknown"
    SINGLE_FILE = "single_file"
    FILE_SET = "file_set"


class BaseMetadataObject:
    content_type = ContentType.UNKNOWN

    def __init__(self, file_object_path: str, file_updated: bool):
        self.file_object_path = file_object_path
        self.file_updated = file_updated

        self.bucket_name = self._bucket_name(file_object_path)
        self.resource_id = self._resource_id(file_object_path)

        self.resource_contents_path = self._resource_contents_path(file_object_path)
        self.resource_md_jsonld_path = self._resource_md_jsonld_path(file_object_path=file_object_path)
        self.resource_md_path = self._resource_md_path(file_object_path=file_object_path)

        self.system_metadata_path = os.path.join(self.resource_md_path, "system_metadata.json")
        self.user_metadata_path = os.path.join(self.resource_md_path, "user_metadata.json")
        self.resource_metadata_jsonld_path = os.path.join(self.resource_md_jsonld_path, "dataset_metadata.json")

        self._resource_associated_media = None

        self.content_type_md_jsonld_path = None
        self.content_type_md_path = None
        self.content_type_contents_path = None
        self.content_type_main_file_path = None
        self.content_type_md_user_path = None

    @property
    def resource_associated_media(self):
        if not self._resource_associated_media:
            self._resource_associated_media = retrieve_file_manifest(
                self.resource_contents_path)
        return self._resource_associated_media

    @classmethod
    def _bucket_name(cls, file_object_path: str) -> str:
        return file_object_path.split('/')[0]

    @classmethod
    def _resource_id(cls, file_object_path: str) -> str:
        return file_object_path.split('/')[1]

    @classmethod
    def _resource_contents_path(cls, file_object_path: str) -> str:
        bucket_name = cls._bucket_name(file_object_path)
        resource_id = cls._resource_id(file_object_path)
        return Template(resource_contents_path_template).safe_substitute(
            bucket_name=bucket_name, resource_id=resource_id)

    @classmethod
    def _resource_md_jsonld_path(cls, file_object_path: str) -> str:
        bucket_name = cls._bucket_name(file_object_path)
        resource_id = cls._resource_id(file_object_path)
        return Template(resource_md_jsonld_path_template).safe_substitute(
            bucket_name=bucket_name, resource_id=resource_id)

    @classmethod
    def _resource_md_path(cls, file_object_path: str) -> str:
        bucket_name = cls._bucket_name(file_object_path)
        resource_id = cls._resource_id(file_object_path)
        return Template(resource_md_path_template).safe_substitute(
            bucket_name=bucket_name, resource_id=resource_id)

    @classmethod
    def _resource_user_metadata_path(cls, file_object_path: str) -> str:
        return os.path.join(cls._resource_md_path(file_object_path), "user_metadata.json")

    @classmethod
    def is_content_type(cls, file_object_path: str) -> bool:
        logging.info(f"Checking if {file_object_path} is of content type {cls.content_type}")
        _, extension = os.path.splitext(file_object_path.lower())
        logging.info(f"Extension is {extension}, valid extensions are {cls._extensions()}")
        return extension in cls._extensions()

    # Methods to be overridden by subclasses below
    @classmethod
    def _extensions(cls) -> list[str]:
        return []

    def content_type_associated_media(self) -> list[MediaObject]:
        return []

    def extract_metadata(self) -> dict:
        return {}

    def clean_up_extracted_metadata(self) -> list:
        # used to cleanup no longer relevant metadata files (e.g. tif files referenced by vrt)
        return []


class FileMetadataObject(BaseMetadataObject):
    def __init__(self, file_object_path: str, file_updated: bool):
        super().__init__(file_object_path, file_updated)
        relative_path = os.path.relpath(self.file_object_path, self.resource_contents_path)
        self.content_type_md_jsonld_path = os.path.join(self.resource_md_jsonld_path, relative_path + ".json")
        self.content_type_md_path = os.path.join(self.resource_md_path, relative_path + ".json")
        self.content_type_contents_path = None
        self.content_type_main_file_path = os.path.join(self.resource_contents_path, relative_path)
        self.content_type_md_user_path = os.path.join(self.resource_md_path, relative_path + ".user_metadata.json")


class FolderMetadataObject(BaseMetadataObject):
    def __init__(self, file_object_path: str, file_updated: bool):
        super().__init__(file_object_path, file_updated)

        parent_directory = os.path.dirname(self.file_object_path)
        relative_path = os.path.relpath(parent_directory, self.resource_contents_path)
        self.content_type_md_jsonld_path = os.path.join(self.resource_md_jsonld_path, relative_path,
                                                        "dataset_metadata.json")
        self.content_type_md_path = os.path.join(self.resource_md_path, relative_path, "user_metadata.json")
        self.content_type_contents_path = os.path.join(self.resource_contents_path, relative_path)
        self.content_type_main_file_path = os.path.join(self.resource_contents_path, relative_path)
        self.content_type_md_user_path = os.path.join(self.resource_md_path, relative_path, ".user_metadata.json")
