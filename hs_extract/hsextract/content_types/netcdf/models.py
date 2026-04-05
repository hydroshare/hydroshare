import os

from hsextract.content_types.models import ContentType, FileMetadataObject
from hsextract.content_types.netcdf.hs_cn_extraction import encode_netcdf
from hsextract.utils.s3 import exists


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
        if extension in cls._extensions():
            # case of data file
            return True
        elif file_object_path.endswith(".nc.user_metadata.json"):
            # case of user metadata file
            relative_path = os.path.relpath(file_object_path, cls._resource_md_path(file_object_path))
            netcdf_file_user_path = os.path.join(cls._resource_md_path(file_object_path),
                                                 relative_path)
            if exists(netcdf_file_user_path):
                return True
            return False
        return False
