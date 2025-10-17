import logging
import os

from hsextract.content_types.models import ContentType, FileMetadataObject
from hsextract.content_types.feature.hs_cn_extraction import encode_vector_metadata


class FeatureMetadataObject(FileMetadataObject):
    content_type = ContentType.FEATURE

    def __init__(self, file_object_path: str, file_updated: bool):
        super().__init__(file_object_path, file_updated)
        # ensure we are working with the .shp file
        file_name, file_extension = os.path.splitext(self.file_object_path.lower())
        if file_extension != ".shp":
            self.file_object_path = file_name + ".shp"
        relative_path = os.path.relpath(self.file_object_path, self.resource_contents_path)
        self.content_type_md_jsonld_path = os.path.join(self.resource_md_jsonld_path, relative_path + ".json")
        self.content_type_md_path = os.path.join(self.resource_md_path, relative_path + ".json")
        self.content_type_contents_path = None
        self.content_type_main_file_path = os.path.join(self.resource_contents_path, relative_path)
        self.content_type_md_user_path = os.path.join(self.resource_md_path, relative_path + ".user_metadata.json")

    @classmethod
    def _extensions(cls) -> list[str]:
        return [".shp", ".shx", ".dbf", ".prj", ".sbx", ".sbn", ".cpg", ".shp.xml", ".fbn", ".fbx", ".ain", ".aih",
                ".atx", ".ixs", ".mxs"]

    @classmethod
    def is_content_type(cls, file_object_path: str) -> bool:
        logging.info(f"Checking if {file_object_path} is of content type {cls.content_type}")
        sub_file_object_path, extension = os.path.splitext(file_object_path.lower())
        if extension == ".xml":
            _, sub_extension = os.path.splitext(sub_file_object_path.lower())
            extension = sub_extension + extension
        logging.info(f"Extension is {extension}, valid extensions are {cls._extensions()}")
        return extension in cls._extensions()

    def content_type_associated_media(self) -> list[dict]:
        media_objects = []
        file_object_name, _ = os.path.splitext(self.file_object_path)
        for m in self.resource_associated_media:
            file_path = m["contentUrl"].split(os.environ.get('AWS_S3_ENDPOINT', ''))[1].strip("/")
            sub_file_name, extension = os.path.splitext(file_path.lower())
            if extension == ".xml":
                sub_file_name, sub_extension = os.path.splitext(sub_file_name.lower())
                extension = sub_extension + extension
            if sub_file_name == file_object_name and extension in self._extensions():
                media_objects.append(m)
        return media_objects

    def extract_metadata(self):
        metadata = encode_vector_metadata(self.file_object_path)
        metadata = metadata.model_dump(exclude_none=True)
        return metadata
