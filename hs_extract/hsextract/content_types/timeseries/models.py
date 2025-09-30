from hsextract.utils.models import ContentType, FileMetadataObject
from hsextract.content_types.timeseries.utils import extract_metadata_csv, extract_metadata


class TimeSeriesMetadataObject(FileMetadataObject):

    content_type = ContentType.TIMESERIES
    
    @classmethod
    def _extensions(cls) -> list[str]:
        return [".csv", ".sqlite"]

    def content_type_associated_media(self):
        return [m for m in self.resource_associated_media if m["contentUrl"].endswith(self.file_object_path)]
    
    def extract_metadata(self):
        if self.file_object_path.endswith(".csv"):
            metadata = extract_metadata_csv(self.file_object_path)
        else:
            metadata = extract_metadata(self.file_object_path)
        return metadata