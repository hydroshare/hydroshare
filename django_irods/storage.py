from io import BytesIO
import os
from pathlib import Path
import tempfile
import zipfile

from django_irods.icommands import SessionException
from django.urls import reverse
from urllib.parse import urlencode

from . import models as m
from .utils import bucket_and_name

from uuid import uuid4

from django.utils.deconstruct import deconstructible
from .s3_backend import S3Storage

# TODO check for usage of these imports elsewhere for cleanup
# from django_irods import icommands
# from .icommands import (
#    Session,
#    GLOBAL_SESSION,
#    GLOBAL_ENVIRONMENT,
#    SessionException,
#    IRodsEnv,
# )


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

    def listdir(self, path):
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
        # TODO this is chicken shits
        additional_directories = [d[len(path.strip("/") + "/"):]
                                  for d in additional_directories
                                  if d[len(path.strip("/") + "/"):] and "/" not in d[len(path.strip("/") + "/"):]]
        directories = list(set(directories + additional_directories))
        return (directories, files, file_sizes)

    def runBagitRule(self, rule_name, input_path, input_resource):
        """
        run iRODS bagit rule which generated bag-releated files without bundling
        :param rule_name: the iRODS rule name to run
        :param input_path: input parameter to the rule that indicates the collection path to
        create bag for
        :param input_resource: input parameter to the rule that indicates the default resource
        to store generated bag files
        :return: None
        """
        # self.session.run("irule", None, "-F", rule_name, input_path, input_resource)
        pass  # TODO

    def zipup(self, in_name, out_name):
        """
        run iRODS ibun command to generate zip file for the bag
        :param in_name: input parameter to indicate the collection path to generate zip
        :param out_name: the output zipped file name
        :return: None
        """
        in_bucket, in_path = bucket_and_name(in_name)
        out_bucket, out_path = bucket_and_name(out_name)
        in_bucket = self.connection.Bucket(in_bucket)

        # Stream zip https://stackoverflow.com/a/69136133
        filesCollection = in_bucket.objects.filter(Prefix=in_path).all()
        archive = BytesIO()

        with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as zip_archive:
            for file in filesCollection:
                relative_path = file.key[len(in_path):]
                with zip_archive.open(relative_path, 'w') as file1:
                    file1.write(file.get()['Body'].read())

        archive.seek(0)
        self.connection.Object(out_bucket, out_path).upload_fileobj(archive)
        archive.close()

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
            return ""

    def _empty_folders(self, resource_id, filter=None):
        folders = self.getAVU(resource_id, "empty_folders").split(",")
        if not folders:
            return []
        if filter:
            folders = [f for f in folders if f.startswith(filter)]
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
        folders.append(path)
        self.setAVU(coll_path, "empty_folders", ",".join(folders))

    def remove_folder(self, res_id, path, AVU_only=False):
        folders = self._empty_folders(res_id)
        for folder in folders:
            if folder.startswith(path):
                folders.remove(folder)
        self.setAVU(res_id, "empty_folders", ",".join(folders))
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
            dst_file_path = src_name.replace(src_name, dest_name)
            res_id = "/".join(dst_file_path.split("/")[:1])
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

        TODO validate this is true
        Note if only directory needs to be created without saving a file, from_name should be empty
        and to_name should have "/" as the last character

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

    def signed_url(self, name):
        super_url = super().url(name.strip("/"))
        if super_url.startswith("http://minio:9000"):  # TODO make this based on DEBUG setting?
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

    def delete_bucket(self, bucket_name):
        try:
            self.connection.delete_bucket(Bucket=bucket_name)
        except Exception:
            pass
