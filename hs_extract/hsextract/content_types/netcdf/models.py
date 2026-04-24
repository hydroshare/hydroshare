import os

from hsextract.content_types.models import ContentType, FileMetadataObject
from hsextract.content_types.netcdf.hs_cn_extraction import encode_netcdf


class NetCDFMetadataObject(FileMetadataObject):
    content_type = ContentType.NETCDF

    @classmethod
    def _extensions(cls) -> list[str]:
        return [".nc"]

    def extract_metadata(self):
        metadata = encode_netcdf(self.file_object_path)
        metadata = metadata.model_dump(exclude_none=True)
        return metadata

    @classmethod
    def is_content_type(cls, file_object_path: str) -> bool:
        _, extension = os.path.splitext(file_object_path.lower())
        return extension in cls._extensions()
