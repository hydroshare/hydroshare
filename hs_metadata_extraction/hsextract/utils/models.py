import os
from pydantic import BaseModel
from enum import Enum

from hsextract.hs_cn_schemas.schema.src.base import MediaObject
from hsextract.utils.s3 import exists, retrieve_file_manifest, write_metadata


class MinIOEvent(BaseModel):
    EventName: str
    Key: str

class ContentType(Enum):
    RASTER = "raster"
    NETCDF = "netcdf"
    ZARR = "zarr"
    FEATURE = "feature"
    REFTIMESERIES = "reftimeseries"
    TIMESERIES = "timeseries"
    UNKNOWN = "unknown"
    SINGLE_FILE = "single_file"
    FILE_SET = "file_set"

class MetadataObject:
    def __init__(self, file_object_path: str, file_updated: bool, resource_contents_path: str = None, resource_md_path: str = None, resource_md_jsonld_path: str = None):
        self.file_object_path = file_object_path
        self.file_updated = file_updated
        
        bucket_name = file_object_path.split('/')[0]
        resource_id = file_object_path.split('/')[1]
        if not resource_contents_path:
            resource_contents_path = f"{bucket_name}/{resource_id}/data/contents"
        if not resource_md_jsonld_path:
            resource_md_jsonld_path = f"{bucket_name}/{resource_id}/.hsjsonld"
        if not resource_md_path:
            resource_md_path = f"{bucket_name}/{resource_id}/.hs"

        self.resource_contents_path = resource_contents_path # bucket/resource_id/data/contents
        self.resource_md_path = resource_md_path # bucket/resource_id/.hs
        self.resource_md_jsonld_path = resource_md_jsonld_path # bucket/resource_id/.hs/jsonld
        self.content_type_md_jsonld_path = None # content type metadata path, e.g. bucket/.md/resource_id/content_type.json
        self._resource_associated_media = None
        self.system_metadata_path = os.path.join(self.resource_md_path, "system_metadata.json")
        self.user_metadata_path = os.path.join(self.resource_contents_path, "hs_user_meta.json")
        self.resource_metadata_path = os.path.join(self.resource_md_jsonld_path, "dataset_metadata.json")
        self.content_type = self.determine_content_type()
        self._determine_paths()

    def _determine_paths(self):
        # content_type_md_path
        parent_directory = os.path.dirname(self.file_object_path)
        relative_path = os.path.relpath(parent_directory, self.resource_contents_path)
        # TODO check directory content types (e.g. fileset, zarr)
        if self.content_type == ContentType.FILE_SET:
            self.content_type_md_jsonld_path = os.path.join(self.resource_md_jsonld_path, relative_path, "dataset_metadata.json")
            self.content_type_md_path = os.path.join(self.resource_md_path, relative_path, "dataset_metadata.json")
            self.content_type_contents_path = os.path.join(self.resource_contents_path, relative_path)
            self.content_type_main_file_path = os.path.join(self.resource_contents_path, relative_path)
            # TODO make this a file in the .hs metadata directory
            self.content_type_md_user_path = os.path.join(self.resource_contents_path, relative_path, "hs_user_meta.json")
        # check all other content types
        elif self.content_type != ContentType.UNKNOWN:
            relative_path = os.path.relpath(self.file_object_path, self.resource_contents_path)
            self.content_type_md_jsonld_path = os.path.join(self.resource_md_jsonld_path, relative_path + ".json")
            self.content_type_md_path = os.path.join(self.resource_md_path, relative_path + ".json")
            self.content_type_contents_path = None # os.path.join(self.resource_root_path, relative_path)
            # assuming all are main files for now
            self.content_type_main_file_path = os.path.join(self.resource_contents_path, relative_path)
            self.content_type_md_user_path = os.path.join(self.resource_contents_path, relative_path + ".hs_user_meta.json")
    
    @property
    def resource_associated_media(self):
        if not self._resource_associated_media:
            self._resource_associated_media = retrieve_file_manifest(self.resource_contents_path)
        return self._resource_associated_media

    def content_type_associated_media(self) -> list[MediaObject]:
        """
        Get a list of media objects associated with this resource.
        """
        media_objects = []
        if self.content_type in [ContentType.SINGLE_FILE, ContentType.NETCDF, ContentType.REFTIMESERIES, ContentType.TIMESERIES]:
            return [m for m in self.resource_associated_media if m["contentUrl"].endswith(self.file_object_path)]
        elif self.content_type in [ContentType.FILE_SET, ContentType.ZARR]:
            return [m for m in self.resource_associated_media if m["contentUrl"].split(os.environ['AWS_S3_ENDPOINT'])[1].strip("/").startswith(self.content_type_contents_path)]
        return media_objects

    def extract_metadata(self) -> dict:
        if self.content_type == ContentType.NETCDF:
            from hsextract.content_types.netcdf.hs_cn_extraction import encode_netcdf
            metadata = encode_netcdf(self.file_object_path).model_dump(exclude_none=True)
        elif self.content_type == ContentType.RASTER:
            from hsextract.content_types.raster.hs_cn_extraction import encode_raster_metadata
            metadata = encode_raster_metadata(self.file_object_path).model_dump(exclude_none=True)
        elif self.content_type == ContentType.FEATURE:
            from hsextract.content_types.feature.hs_cn_extraction import encode_vector_metadata
            metadata = encode_vector_metadata(self.file_object_path).model_dump(exclude_none=True)
        if self.content_type == ContentType.TIMESERIES:
            from hsextract.content_types.timeseries.utils import extract_metadata
            metadata = extract_metadata(self.file_object_path).model_dump(exclude_none=True)
        else:
            return
        write_metadata(self.content_type_md_path, metadata)
    
    _extension_mapping = {
        ".tif": ContentType.RASTER,
        ".tiff": ContentType.RASTER,
        ".vrt": ContentType.RASTER,
        ".nc": ContentType.NETCDF,
        #".zarr": ContentType.ZARR,
        ".shp": ContentType.FEATURE,
        #".reftst.json": ContentType.REFTIMESERIES,
        ".csv": ContentType.TIMESERIES,
        ".sqlite": ContentType.TIMESERIES,
    }
    
    def determine_content_type(self) -> ContentType:
        """
        Determines the content type of the file based on its extension.
        """
        _, extension = os.path.splitext(self.file_object_path.lower())
        content_type = self._extension_mapping.get(extension, ContentType.UNKNOWN)

        if content_type == ContentType.UNKNOWN:
            # check singlefile
            single_file_user_path = self.file_object_path + ".hs_user_meta.json"
            if exists(single_file_user_path):
                return ContentType.SINGLE_FILE
            # check fileset
            parent_directory = os.path.dirname(self.file_object_path)
            while parent_directory:
                file_set_user_path = os.path.join(parent_directory, "hs_user_meta.json")
                if file_set_user_path == self.user_metadata_path:
                    break
                if exists(file_set_user_path):
                    return ContentType.FILE_SET
                parent_directory = os.path.dirname(parent_directory)

        if content_type == ContentType.UNKNOWN:
            # TODO: determine if other steps are necessary
            pass

        return content_type
