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
            try:
                metadata = extract_metadata_csv(self.file_object_path)
            except Exception as e:
                err_msg = f"Failed to extract metadata from CSV file {self.file_object_path}: {str(e)}"
                print(err_msg)
                return None
        else:
            try:
                metadata = extract_metadata(self.file_object_path)
            except Exception as e:
                err_msg = f"Failed to extract metadata from SQLite file {self.file_object_path}: {str(e)}"
                print(err_msg)
                return None
        # TODO: we don't have a schema for timeseries metadata yet, so we are just
        # returning the extracted metadata as a dict.
        # Once we have a schema, we can validate and transform the extracted metadata and return as dict
        return metadata

    @classmethod
    def is_content_type(cls, file_object_path: str) -> bool:
        _, extension = os.path.splitext(file_object_path.lower())
        return extension in cls._extensions()
