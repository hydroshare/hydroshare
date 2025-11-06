import os
from hsextract.content_types.models import ContentType, FileMetadataObject
from hsextract.content_types.raster.hs_cn_extraction import list_tif_files_s3, encode_raster_metadata


class RasterMetadataObject(FileMetadataObject):
    content_type = ContentType.RASTER

    def __init__(self, file_object_path: str, file_updated: bool):
        super().__init__(file_object_path, file_updated)
        vrt_path = self._determine_vrt_path()
        if vrt_path:
            self.file_object_path = vrt_path
        relative_path = os.path.relpath(self.file_object_path, self.resource_contents_path)
        self.content_type_md_jsonld_path = os.path.join(self.resource_md_jsonld_path, relative_path + ".json")
        self.content_type_md_path = os.path.join(self.resource_md_path, relative_path + ".json")
        self.content_type_contents_path = None
        self.content_type_main_file_path = os.path.join(self.resource_contents_path, relative_path)
        self.content_type_md_user_path = os.path.join(self.resource_md_path, relative_path + ".user_metadata.json")

    @classmethod
    def _extensions(cls) -> list[str]:
        return [".tif", ".tiff", ".vrt"]

    def _determine_vrt_path(self) -> str | None:
        if self.file_object_path.endswith(".vrt"):
            return self.file_object_path
        # determine vrt file if a tif file
        if self.file_object_path.endswith(".tif") or self.file_object_path.endswith(".tiff"):
            vrt_paths = []
            directory = os.path.dirname(self.file_object_path)
            for media in self.resource_associated_media:
                vrt_path = media["contentUrl"].split(os.environ['AWS_S3_ENDPOINT_URL'])[1].strip("/")
                if os.path.dirname(vrt_path) == directory and vrt_path.endswith(".vrt"):
                    vrt_paths.append(vrt_path)
            for vrt_path in vrt_paths:
                tif_files = list_tif_files_s3(vrt_path)
                if os.path.basename(self.file_object_path) in tif_files:
                    return vrt_path
        return None

    def content_type_associated_media(self) -> list[dict]:
        media_objects = []
        content_type_files = [self.file_object_path]
        if self.file_object_path.endswith(".vrt"):
            tif_files = list_tif_files_s3(self.file_object_path)
            for f in tif_files:
                content_type_files.append(self.file_object_path.replace(os.path.basename(self.file_object_path), f))
        for media in self.resource_associated_media:
            file_path = media["contentUrl"].split(os.environ['AWS_S3_ENDPOINT_URL'])[1].strip("/")
            if file_path in content_type_files:
                media_objects.append(media)
        return media_objects

    def extract_metadata(self):
        file_to_extract = self.file_object_path
        content_type_media = self.content_type_associated_media()
        vrt_file = [f for f in content_type_media if f["contentUrl"].endswith(".vrt")]
        if vrt_file:
            file_to_extract = vrt_file[0]["contentUrl"].split(os.environ['AWS_S3_ENDPOINT_URL'])[1].strip("/")

        metadata = encode_raster_metadata(file_to_extract)
        metadata = metadata.model_dump(exclude_none=True)
        return metadata

    def clean_up_extracted_metadata(self) -> list[str]:
        if not self.file_object_path.endswith(".vrt"):
            return []
        content_type_media = self.content_type_associated_media()
        tif_files = [f["contentUrl"].split(os.environ['AWS_S3_ENDPOINT_URL'])[1].strip("/")
                     for f in content_type_media
                     if f["contentUrl"].endswith(".tif") or f["contentUrl"].endswith(".tiff")]
        cleanup_files = []
        for f in tif_files:
            relative_path = os.path.relpath(f, self.resource_contents_path)
            content_type_md_jsonld_path = os.path.join(self.resource_md_jsonld_path, relative_path + ".json")
            content_type_md_path = os.path.join(self.resource_md_path, relative_path + ".json")
            cleanup_files.append(content_type_md_jsonld_path)
            cleanup_files.append(content_type_md_path)
        return cleanup_files
