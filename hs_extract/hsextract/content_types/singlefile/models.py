import os

from hsextract.content_types.models import ContentType, FileMetadataObject
from hsextract.utils.s3 import exists


class SingleFileMetadataObject(FileMetadataObject):
    content_type = ContentType.SINGLE_FILE

    def content_type_associated_media(self):
        if not self.is_content_file and self.file_object_path.endswith(".user_metadata.json"):
            md_relative_path = os.path.relpath(self.file_object_path, self.resource_md_path)
            data_file_object_path = md_relative_path[:-len(".user_metadata.json")]
            data_file_object_path = os.path.join(self.resource_contents_path, data_file_object_path)
        else:
            data_file_object_path = self.file_object_path
        return [
            media_object
            for media_object in self.iter_resource_associated_media()
            if self.media_object_path(media_object) == data_file_object_path
        ]

    def extract_metadata(self):
        return {}

    @classmethod
    def is_content_type(cls, file_object_path: str) -> bool:
        if not file_object_path.endswith(".user_metadata.json"):
            relative_path = os.path.relpath(file_object_path, cls._resource_contents_path(file_object_path))
            relative_path += ".user_metadata.json"
        else:
            relative_path = os.path.relpath(file_object_path, cls._resource_md_path(file_object_path))

        single_file_user_path = os.path.join(cls._resource_md_path(file_object_path), relative_path)
        if exists(single_file_user_path):
            return True
        return False
