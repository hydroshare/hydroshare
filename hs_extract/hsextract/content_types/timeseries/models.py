import os

from hsextract.content_types.models import ContentType, FileMetadataObject
from hsextract.content_types.timeseries.utils import extract_metadata_csv, extract_metadata


class TimeSeriesMetadataObject(FileMetadataObject):
    content_type = ContentType.TIMESERIES

    @classmethod
    def _extensions(cls) -> list[str]:
        # TODO: The use of csv here assumes that csv data has to be timeseries data.
        # We probably need a separate CSV content type for non-timeseries csv data
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
        return extension in cls._extensions()
