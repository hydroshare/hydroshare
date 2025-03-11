from io import BytesIO
import os
from pathlib import Path
import tempfile
import zipfile
import logging

from django_irods.icommands import SessionException
from django.urls import reverse
from urllib.parse import urlencode
from django.conf import settings

from smart_open import open
from . import models as m
from .utils import bucket_and_name, normalized_bucket_name, is_metadata_xml_file

from uuid import uuid4

from django.utils.deconstruct import deconstructible
from .s3_backend import S3Storage


folder_delimiter = "|||||||"
logger = logging.getLogger(__name__)


@deconstructible
class IrodsStorage(S3Storage):
    def __init__(self, **settings):
        super().__init__(**settings)

    @property
    def getUniqueTmpPath(self):
        # return a unique temporary path under temporary bucket
        bucket_name = "tmp"
        unique_bucket_path = os.path.join(bucket_name, uuid4().hex)
        return unique_bucket_path

    def download(self, name):
        return self.open(name, mode="rb")

    def listdir(self, path, remove_metadata=False):
        """
        list the contents of the directory
        :param path: the directory path to list
        :return: a list of files in the directory
        """
        folder_path = path.strip("/") + "/"  # ensure a folder is matched
        directories, files, file_sizes = super().listdir(folder_path)
        directories = [d for d in directories if d != os.path.basename(path)]

        resource_id = "/".join(path.split("/")[:1])
        additional_directories = self._empty_folders(resource_id, path)
        if not directories and not files and not additional_directories:
            raise SessionException(f"Path {path} does not exist")
        path = path.strip("/")
        additional_directories = [d[len(path):].strip("/").split("/")[0]
                                  for d in additional_directories
                                  if d[len(path):].strip("/")]
        directories = list(set(directories + additional_directories))

        if remove_metadata:
            # remove .xml metadata files from the list
            files = [f for f in files if not is_metadata_xml_file(f)]

        return (directories, files, file_sizes)

    def zipup(self, in_name, out_name):
        """
        run iRODS ibun command to generate zip file for the bag
        :param in_name: input parameter to indicate the collection path to generate zip
        :param out_name: the output zipped file name
        :return: None
        """
        def chunk_request(zip_archive_file, bucket, key):
            chunk_size = 1024 * 1024 * 256  # 256MB
            object_attrs = self.connection.meta.client.get_object_attributes(Bucket=bucket, Key=key,
                                                                             ObjectAttributes=["ObjectSize"])
            object_size = object_attrs.get("ObjectSize")

            chunk_start = 0
            chunk_end = chunk_start + chunk_size - 1

            while chunk_start < object_size:
                # Read specific byte range from file as a chunk. We do this because AWS server times out and sends
                # empty chunks when streaming the entire file.
                if body := self.connection.meta.client.get_object(
                    Bucket=bucket, Key=key, Range=f"bytes={chunk_start}-{chunk_end}"
                ).get("Body"):
                    chunk = body.read()
                    zip_archive_file.write(chunk)
                    chunk_start += chunk_size
                    chunk_end += chunk_size
                    chunk_end = min(chunk_end, object_size)

        in_bucket_name, in_path = bucket_and_name(in_name)
        out_bucket, out_path = bucket_and_name(out_name)
        in_bucket = self.connection.Bucket(in_bucket_name)

        filesCollection = in_bucket.objects.filter(Prefix=in_path).all()

        in_prefix = os.path.dirname(in_path) if self.isDir(in_name) else in_path
        with open(f's3://{out_bucket}/{out_path}', 'wb', transport_params={'client': self.connection.meta.client}
                  ) as out_file:
            with zipfile.ZipFile(out_file, 'w', zipfile.ZIP_DEFLATED) as zip_archive:
                for file_key in filesCollection:
                    relative_path = file_key.key[len(in_prefix):]
                    with zip_archive.open(relative_path, 'w', force_zip64=True) as zip_archive_file:
                        chunk_request(zip_archive_file, in_bucket_name, file_key.key)

    def unzip(self, zip_file_path, unzipped_folder=""):
        """
        run iRODS ibun command to unzip files into a new folder
        :param zip_file_path: path of the zipped file to be unzipped
        :param unzipped_folder: Optional defaults to the basename of zip_file_path when not
        provided.  The folder to unzip to.
        :return: the folder files were unzipped to
        """

        zip_bucket, zip_name = bucket_and_name(zip_file_path)
        unzipped_bucket, unzipped_path = bucket_and_name(unzipped_folder)

        bucket = self.connection.Bucket(zip_bucket)
        filebytes = BytesIO()
        bucket.download_fileobj(zip_name, filebytes)
        with tempfile.TemporaryDirectory() as extracted_folder:
            with zipfile.ZipFile(filebytes, "r") as zip_ref:
                zip_ref.extractall(extracted_folder)
            for path in Path(extracted_folder).rglob("*"):
                if path.is_dir():
                    continue

                unzipped_file_path = os.path.relpath(path, extracted_folder)
                file_unzipped_path = os.path.join(unzipped_path, unzipped_file_path)
                self.connection.Bucket(unzipped_bucket).upload_file(path, file_unzipped_path)
        return unzipped_folder

    def setAVU(self, name, attName, attVal):
        """
        set AVU in database - this is used for on-demand bagging by indicating
        whether the resource has been modified via AVU pairs

        Parameters:
        :param
        name: the resource collection name to set AVU.
        attName: the attribute name to set
        attVal: the attribute value to set
        """
        m.AVU.objects.update_or_create(name=name, attName=attName, defaults={'attVal': attVal})

    def getAVU(self, name, attName):
        """
        set AVU in database - this is used for on-demand bagging by indicating
        whether the resource has been modified via AVU pairs

        Parameters:
        :param
        name: the resource collection name to set AVU.
        attName: the attribute name to set
        attVal: the attribute value to set
        """
        try:
            return m.AVU.objects.get(name=name, attName=attName).attVal
        except m.AVU.DoesNotExist:
            return None

    def _empty_folders(self, resource_id, filter=None):
        folders = self.getAVU(resource_id, "empty_folders")
        if not folders:
            return []
        folders = folders.split(folder_delimiter)
        if filter:
            if not filter.endswith("/"):
                filter += "/"
            # folders = [f for f in folders if f.startswith(filter) and filter.split("/")[-1] in f.split("/")]
            folders = [f for f in folders if f"{f}/".startswith(filter)]
        return folders

    def exists(self, name):
        if super().exists(name):
            return True
        bucket_name, key = bucket_and_name(name)
        bucket = self.connection.Bucket(bucket_name)
        for f in bucket.objects.filter(Prefix=key):
            if f.key == key:
                return True
            elif f.key.startswith(key.strip("/") + "/"):
                return True

        resource_id_and_relative_path = key.split("/data/contents/")
        resource_id = resource_id_and_relative_path[0]
        empty_dirs = self._empty_folders(resource_id)
        if name in empty_dirs:
            return True

        return False

    def create_folder(self, coll_path, path):
        folders = self._empty_folders(coll_path)
        folders.append(path.strip("/"))
        # remove duplicates
        folders = list(set(folders))
        self.setAVU(coll_path, "empty_folders", folder_delimiter.join(folders))

    def remove_folder(self, res_id, path, AVU_only=False):
        folders = self._empty_folders(res_id)
        for folder in folders:
            if folder.startswith(path):
                folders.remove(folder)
        self.setAVU(res_id, "empty_folders", folder_delimiter.join(folders))
        if not AVU_only:
            src_bucket, src_name = bucket_and_name(path)
            src_name = src_name.strip("/") + "/"
            for file in self.connection.Bucket(src_bucket).objects.filter(Prefix=src_name):
                self.connection.Object(src_bucket, file.key).delete()

    def copyFiles(self, src_path, dest_path, delete_src=False):
        """
        copies an S3 object (file) or files matching a prefix (directory)
        to another data-object or collection

        Parameters:
        :param
        src_path: the iRODS data-object or collection name to be copied from.
        dest_path: the iRODS data-object or collection name to be copied to
        delete_src: delete the source file after copying when set to True. Default is False
        """
        src_bucket, src_name = bucket_and_name(src_path)
        dst_bucket, dest_name = bucket_and_name(dest_path)
        bucket = self.connection.Bucket(src_bucket)

        if self.isFile(src_path):
            self.connection.Bucket(dst_bucket).copy(
                {
                    "Bucket": src_bucket,
                    "Key": src_name,
                },
                dest_name,
            )
            if delete_src:
                self.connection.Object(src_bucket, src_name).delete()
        else:
            # copy files
            for file in bucket.objects.filter(Prefix=src_name):
                src_file_path = file.key
                dst_file_path = file.key.replace(src_name, dest_name)
                self.connection.Bucket(dst_bucket).copy(
                    {
                        "Bucket": src_bucket,
                        "Key": src_file_path,
                    },
                    dst_file_path,
                )
                if delete_src:
                    self.connection.Object(src_bucket, src_file_path).delete()

            # update empty_folders AVU
            res_id = "/".join(dest_name.split("/")[:1])
            for empty_folder in self._empty_folders(res_id, filter=src_name):
                new_folder = empty_folder.replace(src_name, dest_name)
                self.remove_folder(res_id, empty_folder, AVU_only=True)
                self.create_folder(res_id, new_folder)

    def moveFile(self, src_path, dest_path):
        """
        Parameters:
        :param
        src_path: the iRODS data-object or collection name to be moved from.
        dest_path: the iRODS data-object or collection name to be moved to
        moveFile() moves/renames an S3 object (file) or prefix (directory) to another data-object or collection
        """
        self.copyFiles(src_path, dest_path, delete_src=True)

    def save_md5_manifest(self, resource_id):
        """
        save md5 manifest file for the resource
        :param resource_id: the resource id
        """
        bucket_name, path_name = bucket_and_name(resource_id)
        bucket = self.connection.Bucket(bucket_name)
        checksums = []
        strip_length = len(resource_id + "/")
        for file in bucket.objects.filter(Prefix=os.path.join(path_name, "data")):
            checksums.append({file.key[strip_length:]: file.e_tag.strip('"')})
        with tempfile.NamedTemporaryFile() as f:
            for checksum in checksums:
                f.write(f"{list(checksum.values())[0]}    {list(checksum.keys())[0]}\n".encode())
            f.flush()
            self.saveFile(f.name, f"{resource_id}/manifest-md5.txt")

    def saveFile(self, src_local_file, dest_s3_bucket_path):
        """
        Parameters:
        :param
        src_local_file: the temporary file name in local disk to be uploaded from.
        dest_s3_bucket_path: the data object path in iRODS to be uploaded to
        """
        dst_bucket, dst_name = bucket_and_name(dest_s3_bucket_path)
        self.connection.Bucket(dst_bucket).upload_file(src_local_file, dst_name)

    def checksum(self, s3_bucket_name):
        """
        Compute/Update checksum of file object and return the checksum
        :param s3_bucket_name: the data object name with full collection path in order to locate
        data object from current working directory
        :return: checksum of the file object
        """
        bucket, name = bucket_and_name(s3_bucket_name)
        s3_object = self.connection.Object(bucket, name)
        return s3_object.e_tag.strip('"')

    def download_file(self, s3_bucket_name, local_file_path):
        """
        Download file from S3 bucket to local file path
        :param s3_bucket_name: the data object name with full collection path in order to locate data object from
        current working directory
        :param local_file_path: the local file path to download the file to
        """
        bucket, name = bucket_and_name(s3_bucket_name)
        self.connection.Bucket(bucket).download_file(name, local_file_path)

    def signed_url(self, name, **kwargs):
        super_url = super().url(name.strip("/"), kwargs)
        # check AWS_S3_USE_LOCAL setting to determine if we should return local url
        use_local = getattr(settings, "AWS_S3_USE_LOCAL", False)
        if use_local and not settings.TESTING:
            return super_url.replace("http://minio:9000", "http://localhost:9000")
        return super_url

    def url(self, name, url_download=False, zipped=False, aggregation=False):
        reverse_url = reverse("rest_download", kwargs={"path": name})
        query_params = {
            "url_download": url_download,
            "zipped": zipped,
            "aggregation": aggregation,
        }
        return reverse_url + "?" + urlencode(query_params)

    def isDir(self, path):
        try:
            self.listdir(path)
        except SessionException:
            return False
        return True

    def isFile(self, path):
        src_bucket, src_name = bucket_and_name(path)
        try:
            self.connection.Object(src_bucket, src_name).load()
            return True
        except Exception:
            # TODO check if something went wrong vs not found
            return False

    def create_bucket(self, bucket_name):
        try:
            self.connection.create_bucket(Bucket=bucket_name)
        except Exception:
            pass
            # logger.exception(f"Failed to create bucket {bucket_name}")

    def delete_bucket(self, bucket_name):
        try:
            self.connection.meta.client.delete_bucket(Bucket=bucket_name)
        except Exception:
            pass
            # logger.exception(f"Failed to delete bucket {bucket_name}")

    def new_quota_holder(self, resource_id, new_quota_holder_id):
        """
        Create a new bucket for the resource
        :param resource_id: the resource id
        """
        src_bucket, src_name = bucket_and_name(resource_id)
        dst_bucket = normalized_bucket_name(new_quota_holder_id)
        dest_name = src_name

        bucket = self.connection.Bucket(src_bucket)
        files_to_delete = []
        for file in bucket.objects.filter(Prefix=src_name):
            src_file_path = file.key
            dst_file_path = file.key.replace(src_name, dest_name)
            self.connection.Bucket(dst_bucket).copy(
                {
                    "Bucket": src_bucket,
                    "Key": src_file_path,
                },
                dst_file_path,
            )
            files_to_delete.append(src_file_path)

        for src_file_path in files_to_delete:
            self.connection.Object(src_bucket, src_file_path).delete()

    def bucket_exists(self, bucket_name):
        try:
            self.connection.meta.client.head_bucket(Bucket=bucket_name)
            return True
        except Exception:
            return False
