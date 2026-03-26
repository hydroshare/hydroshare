from hsextract.content_types.models import ContentType, FileMetadataObject
from hsextract.content_types.timeseries.utils import extract_metadata_csv, extract_metadata


class TimeSeriesMetadataObject(FileMetadataObject):
    content_type = ContentType.TIMESERIES

    @classmethod
    def _extensions(cls) -> list[str]:
        return [".csv", ".sqlite"]

    def content_type_associated_media(self):
        return [
            media_object
            for media_object in self.iter_resource_associated_media()
            if self.media_object_path(media_object) == self.file_object_path
        ]

    def extract_metadata(self):
        if self.file_object_path.endswith(".csv"):
            metadata = extract_metadata_csv(self.file_object_path)
        else:
            metadata = extract_metadata(self.file_object_path)
        return metadata
