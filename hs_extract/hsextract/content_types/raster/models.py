import os
from hsextract.content_types.models import ContentType, FileMetadataObject
from hsextract.content_types.raster.hs_cn_extraction import list_tif_files_s3, encode_raster_metadata
from hsextract.utils.s3 import exists


class RasterMetadataObject(FileMetadataObject):
    content_type = ContentType.RASTER

    def __init__(self, file_object_path: str, file_updated: bool, file_user_meta: bool = False):
        super().__init__(file_object_path, file_updated, file_user_meta)
        self._content_type_associated_media = None
        vrt_path = self._determine_vrt_path()
        if vrt_path:
            self.file_object_path = vrt_path
        if file_user_meta and self.file_object_path.endswith(".user_metadata.json"):
            relative_path = os.path.relpath(self.file_object_path, self.resource_md_path)
            relative_path = relative_path[:-len(".user_metadata.json")]
        else:
            relative_path = os.path.relpath(self.file_object_path, self.resource_contents_path)
        file_parent_directory = os.path.dirname(relative_path)
        self.content_type_md_jsonld_path = os.path.join(self.resource_md_jsonld_path, relative_path + ".json")
        self.content_type_md_path = os.path.join(self.resource_md_path, relative_path + ".json")
        self.content_type_contents_path = os.path.join(self.resource_contents_path, file_parent_directory)
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
            for media_object in self.iter_resource_associated_media():
                vrt_path = self.media_object_path(media_object)
                if os.path.dirname(vrt_path) == directory and vrt_path.endswith(".vrt"):
                    vrt_paths.append(vrt_path)
            for vrt_path in vrt_paths:
                tif_files = list_tif_files_s3(vrt_path)
                if os.path.basename(self.file_object_path) in tif_files:
                    return vrt_path
        return None

    def content_type_associated_media(self) -> list[dict]:
        if self._content_type_associated_media is not None:
            return self._content_type_associated_media

        media_objects = []
        file_path = os.path.join(self.content_type_contents_path, self.get_file_name())
        folder_path = self.get_folder_path()
        content_type_files = {file_path}
        if file_path.endswith(".vrt"):
            tif_files = list_tif_files_s3(file_path)
            for f in tif_files:
                content_type_files.add(file_path.replace(os.path.basename(file_path), f))
        for media_object in self.iter_resource_associated_media(folder_path=folder_path):
            file_path = self.media_object_path(media_object)
            if file_path in content_type_files:
                media_objects.append(media_object)
                if len(media_objects) == len(content_type_files):
                    break
        self._content_type_associated_media = media_objects
        return self._content_type_associated_media

    def extract_metadata(self):
        file_to_extract = self.file_object_path
        content_type_media = self.content_type_associated_media()
        vrt_file = [f for f in content_type_media if f["contentUrl"].endswith(".vrt")]
        if vrt_file:
            file_to_extract = self.media_object_path(vrt_file[0])

        metadata = encode_raster_metadata(file_to_extract)
        metadata = metadata.model_dump(exclude_none=True)
        return metadata

    def clean_up_extracted_metadata(self) -> list[str]:
        if not self.file_object_path.endswith(".vrt"):
            return []
        content_type_media = self.content_type_associated_media()
        tif_files = [self.media_object_path(f)
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
    
    @classmethod
    def is_content_type(cls, file_object_path: str) -> bool:
        _, extension = os.path.splitext(file_object_path.lower())
        if extension in cls._extensions():
            # case of data file
            return True
        elif file_object_path.endswith(".vrt.user_metadata.json") \
            or file_object_path.endswith(".tif.user_metadata.json") \
            or file_object_path.endswith(".tiff.user_metadata.json"):
            # case of user metadata file
            relative_path = os.path.relpath(file_object_path, cls._resource_md_path(file_object_path))
            raster_file_user_path = os.path.join(cls._resource_md_path(file_object_path),
                                                 relative_path)
            if exists(raster_file_user_path):
                return True
            return False
        return False
