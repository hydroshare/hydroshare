import os

from hsextract.utils.models import ContentType, FileMetadataObject


class FeatureMetadataObject(FileMetadataObject):
    content_type = ContentType.FEATURE

    @classmethod
    def _extensions(cls) -> list[str]:
        return [".shp", ".shx", ".dbf", ".prj"]

    def content_type_associated_media(self) -> list[dict]:
        media_objects = []
        for m in self.resource_associated_media:
            file_path = m["contentUrl"].split(os.environ.get('AWS_S3_ENDPOINT', ''))[1].strip("/")
            _, extension = os.path.splitext(file_path.lower())
            if file_path.endswith(self.file_object_path) and extension in self._extensions():
                media_objects.append(m)
        return media_objects

    def extract_metadata(self):
        # TODO finding an issue importing encode_vector_metadata at file level
        from hsextract.content_types.feature.hs_cn_extraction import encode_vector_metadata
        # TODO do all the files need to be present for extraction?
        # e.g. shp, shx, dbf, prj
        file_name, _ = os.path.splitext(self.file_object_path.lower())
        shp_file_object_path = f"{file_name}.shp"
        metadata = encode_vector_metadata(shp_file_object_path)
        metadata = metadata.model_dump(exclude_none=True)
        return metadata
