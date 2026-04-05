import os
from hsextract.content_types.models import ContentType, FolderMetadataObject
from hsextract.utils.s3 import exists


class FileSetMetadataObject(FolderMetadataObject):
    content_type = ContentType.FILE_SET

    def content_type_associated_media(self):
        if self._content_type_associated_media is not None:
            return self._content_type_associated_media
        self._content_type_associated_media = [
            media_object
            for media_object in self.iter_resource_associated_media()
            if self.media_object_path(media_object).startswith(self.content_type_contents_path)
        ]
        return self._content_type_associated_media

    def extract_metadata(self):
        return {}

    @classmethod
    def is_content_type(cls, file_object_path: str) -> bool:
        resource_user_metadata_path = cls._resource_user_metadata_path(file_object_path)
        base_md_path = cls._resource_md_path(file_object_path)
        if file_object_path.endswith("user_metadata.json"):
            relative_path = os.path.relpath(file_object_path, base_md_path)
        else:
            relative_path = os.path.relpath(file_object_path, cls._resource_contents_path(file_object_path))
        parent_directory = os.path.dirname(relative_path)

        while parent_directory:
            fileset_user_path = os.path.join(base_md_path, parent_directory, "user_metadata.json")
            if fileset_user_path == resource_user_metadata_path:
                return False
            if exists(fileset_user_path):
                return True
            parent_directory = os.path.dirname(parent_directory)

        return False
