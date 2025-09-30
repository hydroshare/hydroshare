import os
import logging
from hsextract.utils.models import ContentType, FolderMetadataObject
from hsextract.utils.s3 import exists


class FileSetMetadataObject(FolderMetadataObject):
    content_type = ContentType.FILE_SET

    def content_type_associated_media(self):
        return [m for m in self.resource_associated_media
                if m["contentUrl"].split(os.environ.get('AWS_S3_ENDPOINT', ''))[1].strip("/").startswith(
                    self.content_type_contents_path)]

    def extract_metadata(self):
        return {}

    @classmethod
    def is_content_type(cls, file_object_path: str) -> bool:
        logging.info(f"Checking if fileset for {file_object_path}")
        resource_user_metadata_path = cls._resource_user_metadata_path(file_object_path)
        relative_path = os.path.relpath(file_object_path, cls._resource_contents_path(file_object_path))
        parent_directory = os.path.dirname(relative_path)
        while parent_directory:
            fileset_user_path = os.path.join(cls._resource_md_path(file_object_path),
                                             parent_directory, "user_metadata.json")
            parent_directory = os.path.dirname(parent_directory)
            if exists(fileset_user_path):
                return True
            if fileset_user_path == resource_user_metadata_path:
                return False
