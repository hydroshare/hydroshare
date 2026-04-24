import os

from hsextract.content_types.models import ContentType, FileMetadataObject
from hsextract.utils.s3 import exists


class SingleFileMetadataObject(FileMetadataObject):
    content_type = ContentType.SINGLE_FILE

    def extract_metadata(self):
        return {}

    @classmethod
    def is_content_type(cls, file_object_path: str) -> bool:
        relative_path = os.path.relpath(file_object_path, cls._resource_contents_path(file_object_path))
        single_file_user_path = os.path.join(cls._resource_md_path(file_object_path),
                                             relative_path + ".user_metadata.json")
        if exists(single_file_user_path):
            return True
        return False
