import os
import zipfile
from pathlib import Path

from django.core.files.uploadedfile import UploadedFile

from hs_core.hydroshare import add_resource_files


class MyTemporaryUploadedFile(UploadedFile):
    def __init__(self, file=None, name=None, content_type=None, size=None, charset=None, content_type_extra=None):
        super(UploadedFile, self).__init__(file, name)
        self.orig_name = name
        self.size = size
        self.content_type = content_type
        self.charset = charset
        self.content_type_extra = content_type_extra

    def temporary_file_path(self):
        return self.orig_name


def prepare_resource(folder, res, user, extracted_directory, test_bag_path):
    from hs_core.views.utils import unzip_file

    def zip_up(ziph, root_directory, directory=""):
        full_path = Path(os.path.join(root_directory, directory))
        dirs = [str(item) for item in full_path.iterdir() if item.is_dir()]
        files = [str(item) for item in full_path.iterdir() if item.is_file()]
        for file in files:
            ziph.write(file, arcname=os.path.join(directory, os.path.basename(file)))
        for d in dirs:
            zip_up(ziph, root_directory, os.path.join(directory, os.path.basename(d)))

    zipf = zipfile.ZipFile(test_bag_path, 'w')
    zip_up(zipf, os.path.join(extracted_directory, folder))

    bag_file_name = os.path.basename(test_bag_path)
    files_to_upload = [UploadedFile(file=open(test_bag_path, 'rb'),
                                    name=bag_file_name)]
    add_resource_files(res.short_id, *files_to_upload, full_paths={})

    unzip_file(user, res.short_id, "data/contents/" + bag_file_name, True,
               overwrite=True, auto_aggregate=True, ingest_metadata=True)

    res.refresh_from_db()