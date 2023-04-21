import os
import shutil

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


def prepare_resource(folder, res, user, extracted_directory, test_bag_path, upload_to=""):
    from hs_core.views.utils import unzip_file

    dir_to_zip = os.path.join(extracted_directory, folder)
    # remove '.zip' extension from the zip file path as the extension will be added by make_archive call
    zip_to_file_path = test_bag_path[:-4]
    shutil.make_archive(zip_to_file_path, 'zip', dir_to_zip)

    bag_file_name = os.path.basename(test_bag_path)
    files_to_upload = [UploadedFile(file=open(test_bag_path, 'rb'),
                                    name=bag_file_name)]
    add_resource_files(res.short_id, *files_to_upload, full_paths={}, folder=upload_to)

    if upload_to:
        zip_file_path = os.path.join("data", "contents", upload_to, bag_file_name)
    else:
        zip_file_path = os.path.join("data", "contents", bag_file_name)

    unzip_file(user, res.short_id, zip_file_path, True,
               overwrite=True, auto_aggregate=True, ingest_metadata=True)

    res.refresh_from_db()
