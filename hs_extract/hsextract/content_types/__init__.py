from hsextract.content_types.raster.models import RasterMetadataObject
from hsextract.content_types.singlefile.models import SingleFileMetadataObject
from hsextract.content_types.fileset.models import FileSetMetadataObject
from hsextract.content_types.timeseries.models import TimeSeriesMetadataObject
from hsextract.content_types.netcdf.models import NetCDFMetadataObject
from hsextract.content_types.feature.models import FeatureMetadataObject
from hsextract.content_types.models import BaseMetadataObject, SystemMetadataObject, ResourceUserMetadataObject

metadata_classes = [
    RasterMetadataObject,
    TimeSeriesMetadataObject,
    NetCDFMetadataObject,
    FeatureMetadataObject,
    # single file and fileset go last since they are more general
    SingleFileMetadataObject,
    FileSetMetadataObject,
    SystemMetadataObject,
    ResourceUserMetadataObject
]


def determine_metadata_object(file_object_path: str, file_updated: bool) -> BaseMetadataObject:
    for metadata_class in metadata_classes:
        if metadata_class.is_content_type(file_object_path):
            return metadata_class(file_object_path, file_updated)
    return BaseMetadataObject(file_object_path, file_updated)
