import os

from hsextract.content_types.models import ContentType, FileMetadataObject
from hsextract.content_types.timeseries.utils import extract_metadata_csv, extract_metadata
from hsextract.utils.s3 import exists


class TimeSeriesMetadataObject(FileMetadataObject):
    content_type = ContentType.TIMESERIES

    @classmethod
    def _extensions(cls) -> list[str]:
        # TODO: Should we stop supporting csv and only support sqlite for timeseries content type?
        # Also we will be using '.csv' extension for CSV content type when we implement
        # a MetadataObject for that content type.
        return [".csv", ".sqlite"]

    def extract_metadata(self):
        if self.file_object_path.endswith(".csv"):
            metadata = extract_metadata_csv(self.file_object_path)
        else:
            metadata = extract_metadata(self.file_object_path)
        return metadata

    @classmethod
    def is_content_type(cls, file_object_path: str) -> bool:
        _, extension = os.path.splitext(file_object_path.lower())
        if extension in cls._extensions():
            # case of data file
            return True
        elif (
            file_object_path.endswith(".csv.user_metadata.json")
            or file_object_path.endswith(".sqlite.user_metadata.json")
        ):
            # case of user metadata file
            relative_path = os.path.relpath(file_object_path, cls._resource_md_path(file_object_path))
            timeseries_file_user_path = os.path.join(cls._resource_md_path(file_object_path),
                                                     relative_path)
            if exists(timeseries_file_user_path):
                return True
            return False
        return False
