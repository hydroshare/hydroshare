import os
from typing import Union

from hsextract.content_types.raster.models import RasterMetadataObject
from hsextract.content_types.singlefile.models import SingleFileMetadataObject
from hsextract.content_types.fileset.models import FileSetMetadataObject
from hsextract.content_types.timeseries.models import TimeSeriesMetadataObject
from hsextract.content_types.netcdf.models import NetCDFMetadataObject
from hsextract.content_types.feature.models import FeatureMetadataObject
from hsextract.content_types.models import BaseMetadataObject


metadata_classes = [
    RasterMetadataObject,
    TimeSeriesMetadataObject,
    NetCDFMetadataObject,
    FeatureMetadataObject,
    # single file and fileset go last since they are more general
    SingleFileMetadataObject,
    FileSetMetadataObject
]

ReturnMetaObjectType = Union[
    RasterMetadataObject,
    TimeSeriesMetadataObject,
    NetCDFMetadataObject,
    FeatureMetadataObject,
    SingleFileMetadataObject,
    FileSetMetadataObject,
    BaseMetadataObject
]


def determine_metadata_object(file_object_path: str, file_updated: bool) -> ReturnMetaObjectType:
    for metadata_class in metadata_classes:
        if metadata_class.is_content_type(file_object_path):
            return metadata_class(file_object_path, file_updated)
    return BaseMetadataObject(file_object_path, file_updated)


def determine_metadata_object_from_user_metadata(
        user_metadata_file_path: str, file_updated: bool
) -> ReturnMetaObjectType:
    if not user_metadata_file_path.endswith("user_metadata.json"):
        return BaseMetadataObject(user_metadata_file_path, file_updated)

    bucket_path, relative_user_meta_path = user_metadata_file_path.split("/.hsmetadata/", 1)
    is_fileset_user_metadata = False
    if user_metadata_file_path.endswith("/user_metadata.json"):
        is_fileset_user_metadata = True
        # fileset user metadata
        relative_content_path = relative_user_meta_path[:-len("/user_metadata.json")]
    else:
        # all other content type user metadata
        relative_content_path = relative_user_meta_path[:-len(".user_metadata.json")]
    content_path = os.path.join(bucket_path, "data", "contents", relative_content_path)
    if not is_fileset_user_metadata:
        # check content path exists, if not return BaseMetadataObject (unknown content type)
        from hsextract.utils.s3 import exists
        if not exists(content_path):
            return BaseMetadataObject(content_path, file_updated)
    return determine_metadata_object(content_path, file_updated)
