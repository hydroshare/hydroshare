from hsextract.utils.models import ContentType, FileMetadataObject
from hsextract.content_types.netcdf.hs_cn_extraction import encode_netcdf


class NetCDFMetadataObject(FileMetadataObject):
    content_type = ContentType.NETCDF

    @classmethod
    def _extensions(cls) -> list[str]:
        return [".nc"]

    def content_type_associated_media(self):
        return [m for m in self.resource_associated_media if m["contentUrl"].endswith(self.file_object_path)]

    def extract_metadata(self):
        metadata = encode_netcdf(self.file_object_path)
        metadata = metadata.model_dump(exclude_none=True)
        return metadata
