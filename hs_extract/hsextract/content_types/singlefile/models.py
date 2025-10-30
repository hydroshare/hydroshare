import logging
import os

from hsextract.content_types.models import ContentType, FileMetadataObject
from hsextract.utils.s3 import exists


class SingleFileMetadataObject(FileMetadataObject):
    content_type = ContentType.SINGLE_FILE

    def content_type_associated_media(self):
        return [m for m in self.resource_associated_media if m["contentUrl"].endswith(self.file_object_path)]

    def extract_metadata(self):
        return {}

    @classmethod
    def is_content_type(cls, file_object_path: str) -> bool:
        print(f"Checking if {file_object_path} is of content type {cls.content_type}")
        relative_path = os.path.relpath(file_object_path, cls._resource_contents_path(file_object_path))
        print(f"Relative path for {file_object_path} is {relative_path}")
        # check singlefile
        single_file_user_path = os.path.join(cls._resource_md_path(file_object_path),
                                             relative_path + ".user_metadata.json")
        print(f"Checking for single file user metadata at {single_file_user_path}")
        if exists(single_file_user_path):
            print(f"Found user metadata for {file_object_path} at {single_file_user_path}")
            return True
        print(f"No user metadata found for {file_object_path}")
        return False
