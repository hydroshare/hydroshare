import os

from hsextract.content_types.models import ContentType, FileMetadataObject
from hsextract.content_types.feature.hs_cn_extraction import encode_vector_metadata
from hsextract.utils.s3 import exists


class FeatureMetadataObject(FileMetadataObject):
    content_type = ContentType.FEATURE

    def __init__(self, file_object_path: str, file_updated: bool, file_user_meta: bool = False):
        super().__init__(file_object_path, file_updated, file_user_meta)
        if file_user_meta and self.file_object_path.endswith(".user_metadata.json"):
            relative_path = os.path.relpath(self.file_object_path, self.resource_md_path)
            relative_path = relative_path[:-len(".user_metadata.json")]
        else:
            # ensure we are working with the .shp file
            file_name, file_extension = os.path.splitext(self.file_object_path.lower())
            if file_extension != ".shp":
                if file_extension == ".xml":
                    sub_file_name, _ = os.path.splitext(file_name)
                    self.file_object_path = sub_file_name + ".shp"
                else:
                    self.file_object_path = file_name + ".shp"
            relative_path = os.path.relpath(self.file_object_path, self.resource_contents_path)
        file_parent_directory = os.path.dirname(relative_path)
        self.content_type_md_jsonld_path = os.path.join(self.resource_md_jsonld_path, relative_path + ".json")
        self.content_type_md_path = os.path.join(self.resource_md_path, relative_path + ".json")
        self.content_type_contents_path = os.path.join(self.resource_contents_path, file_parent_directory)
        self.content_type_main_file_path = os.path.join(self.resource_contents_path, relative_path)
        self.content_type_md_user_path = os.path.join(self.resource_md_path, relative_path + ".user_metadata.json")

    @classmethod
    def _extensions(cls) -> list[str]:
        return [".shp", ".shx", ".dbf", ".prj", ".sbx", ".sbn", ".cpg", ".shp.xml", ".fbn", ".fbx", ".ain", ".aih",
                ".atx", ".ixs", ".mxs"]

    @classmethod
    def is_content_type(cls, file_object_path: str) -> bool:
        sub_file_object_path, extension = os.path.splitext(file_object_path.lower())
        if extension != ".json":
            # case of data file
            if extension == ".xml":
                _, sub_extension = os.path.splitext(sub_file_object_path.lower())
                extension = sub_extension + extension
            return extension in cls._extensions()
        else:
            # case of user metadata file
            if file_object_path.endswith(".shp.user_metadata.json"):
                relative_path = os.path.relpath(file_object_path, cls._resource_md_path(file_object_path))
                feature_file_user_path = os.path.join(cls._resource_md_path(file_object_path), relative_path)
                if exists(feature_file_user_path):
                    return True
                return False
        return False

    def content_type_associated_media(self) -> list[dict]:
        if self._content_type_associated_media is not None:
            return self._content_type_associated_media

        data_file_name = self.get_file_name()
        folder_path = self.get_folder_path()
        if data_file_name.endswith(".shp.xml"):
            data_file_name = data_file_name[:-4]
        file_name, _ = os.path.splitext(data_file_name)
        expected_associated_files = {file_name + ext for ext in self._extensions()}
        expected_associated_file_paths = (
            {os.path.join(self.content_type_contents_path, f) for f in expected_associated_files}
        )
        media_objects = []
        for media_object in self.iter_resource_associated_media(folder_path=folder_path):
            file_path = self.media_object_path(media_object)
            if file_path in expected_associated_file_paths:
                media_objects.append(media_object)
                if len(media_objects) == len(expected_associated_file_paths):
                    break
        self._content_type_associated_media = media_objects
        return self._content_type_associated_media

    def extract_metadata(self):
        metadata = encode_vector_metadata(self.file_object_path)
        metadata = metadata.model_dump(exclude_none=True)
        return metadata
