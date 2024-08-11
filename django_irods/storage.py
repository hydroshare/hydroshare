from io import BytesIO
import os
import zipfile

from . import models as m
from .utils import bucket_and_name

from uuid import uuid4
from django.urls import reverse
from urllib.parse import urlencode

from django.utils.deconstruct import deconstructible
from .s3_backend import S3Storage

# TODO check for usage of these imports elsewhere for cleanup
#from django_irods import icommands
#from .icommands import (
#    Session,
#    GLOBAL_SESSION,
#    GLOBAL_ENVIRONMENT,
#    SessionException,
#    IRodsEnv,
#)


@deconstructible
class IrodsStorage(S3Storage):
    def __init__(self, **settings):
        super().__init__(**settings)
        pass #TODO

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
        directories, files = super().listdir(path)
        resource_id = "/".join(path.split("/")[:1])
        additional_directories = self._empty_folders(resource_id, path)
        # TODO this is chicken shits
        additional_directories = [d[len(path) + 1:] for d in additional_directories if d[len(path) + 1:] and "/" not in d[len(path) + 1:]]
        file_sizes = []
        directories = list(set(directories + additional_directories))
        for f in files:
            # TODO get file size
            file_sizes.append(0)
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
        #self.session.run("irule", None, "-F", rule_name, input_path, input_resource)
        pass #TODO

    def zipup(self, in_name, out_name):
        """
        run iRODS ibun command to generate zip file for the bag
        :param in_name: input parameter to indicate the collection path to generate zip
        :param out_name: the output zipped file name
        :return: None
        """
        in_bucket, in_name = bucket_and_name(in_name)
        out_bucket, out_name = bucket_and_name(out_name)
        in_bucket = self.connection.Bucket(in_bucket)

        # Stream zip https://stackoverflow.com/a/69136133
        filesCollection = in_bucket.objects.filter(Prefix=in_name).all()
        archive = BytesIO()

        with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as zip_archive:
            for file in filesCollection:
                with zip_archive.open(file.key, 'w') as file1:
                    file1.write(file.get()['Body'].read())

        archive.seek(0)
        self.connection.Object(out_bucket, out_name).upload_fileobj(archive)
        archive.close()

    def unzip(self, zip_file_path, unzipped_folder=""):
        """
        run iRODS ibun command to unzip files into a new folder
        :param zip_file_path: path of the zipped file to be unzipped
        :param unzipped_folder: Optional defaults to the basename of zip_file_path when not
        provided.  The folder to unzip to.
        :return: the folder files were unzipped to
        """

        #abs_path = os.path.dirname(zip_file_path)
        #if not unzipped_folder:
        #    unzipped_folder = abs_path
        #else:
        #    unzipped_folder = self._get_nonexistant_path(
        #        os.path.join(abs_path, unzipped_folder)
        #    )

        #self.session.run("ibun", None, "-xDzip", zip_file_path, unzipped_folder)
        #return unzipped_folder
        pass #TODO

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
        #m.AVU(name=name, attName=attName, attVal=attVal).save()

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
        return m.AVU.objects.get(name=name, attName=attName).attVal

    def _empty_folders(self, resource_id, filter=None):
        try:
            folders = self.getAVU(resource_id, "empty_folders").split(",")
        except Exception:
            print(f"no avu found {resource_id}")
            # TODO handle exception specific to empty matching AVU not found
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

    def remove_folder(self, coll_path, path):
        folders = self._empty_folders(coll_path)
        if path in folders:
            folders.remove(path)
        self.setAVU(coll_path, "empty_folders", ",".join(folders))
        src_bucket, src_name = bucket_and_name(path)
        self.connection.Object(src_bucket, src_name).delete()

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
        for file in bucket.objects.filter(Prefix=src_name):
            src_file_path = file.key
            src_name_length = len(src_name)
            src_file_relative_path = src_file_path[:-src_name_length]
            dst_file_path = os.path.join(src_file_relative_path, dest_name)
            self.connection.Bucket(dst_bucket).copy(
                {
                    "Bucket": src_bucket,
                    "Key": src_file_path,
                },
                dst_file_path,
            )
            if delete_src:
                self.connection.Object(src_bucket, src_file_path).delete()

    def moveFile(self, src_path, dest_path):
        """
        Parameters:
        :param
        src_path: the iRODS data-object or collection name to be moved from.
        dest_path: the iRODS data-object or collection name to be moved to
        moveFile() moves/renames an S3 object (file) or prefix (directory) to another data-object or collection
        """
        self.copyFiles(src_path, dest_path, delete_src=True)

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
        :param s3_bucket_name: the data object name with full collection path in order to locate data object from current
        working directory
        :return: checksum of the file object
        """
        # https://stackoverflow.com/questions/16872679/how-to-programmatically-get-the-md5-checksum-of-amazon-s3-file-using-boto
        bucket, name = bucket_and_name(s3_bucket_name)
        s3_object = self.connection.Object(bucket, name)
        return s3_object.e_tag.strip('"')
    
    def download_file(self, s3_bucket_name, local_file_path):
        """
        Download file from S3 bucket to local file path
        :param s3_bucket_name: the data object name with full collection path in order to locate data object from current
        working directory
        :param local_file_path: the local file path to download the file to
        """
        bucket, name = bucket_and_name(s3_bucket_name)
        self.connection.Bucket(bucket).download_file(name, local_file_path)

    def url(self, name):
        super_url = super().url(name.strip("/"))
        return super_url
        # TODO work out zipped downloads
        #reverse_url = reverse("rest_download", kwargs={"path": name})
        #query_params = {
        #    "url_download": url_download,
        #    "zipped": zipped,
        #    "aggregation": aggregation,
        #}
        #return reverse_url + "?" + urlencode(query_params)

    def isDir(self, path):
        dir_prefix = os.path.join(path, "")
        _, files, _ = self.listdir(dir_prefix)
        return  len(files) > 0

    def isFile(self, path):
        src_bucket, src_name = bucket_and_name(path)
        try:
            self.connection.Object(src_bucket, src_name).load()
            return True
        except:
            #TODO check if something went wrong vs not found
            return False
