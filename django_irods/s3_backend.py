import os
import posixpath
from datetime import datetime
from datetime import timedelta
from urllib.parse import urlencode
from .utils import bucket_and_name

from django.core.exceptions import ImproperlyConfigured, SuspiciousOperation
from django.utils.deconstruct import deconstructible
from django.utils.encoding import filepath_to_uri
from django.utils.timezone import make_naive

from storages.backends import s3
from storages.utils import ReadBytesWrapper
from storages.utils import clean_name
from storages.utils import is_seekable
from storages.utils import setting

try:
    from botocore.exceptions import ClientError
except ImportError as e:
    raise ImproperlyConfigured("Could not load Boto3's S3 bindings. %s" % e)


@deconstructible
class S3File(s3.S3File):
    """
    Extends storages.backends.s3.S3File to support files across buckets
    """

    def __init__(self, name, mode, storage, buffer_size=None):
        if "r" in mode and "w" in mode:
            raise ValueError("Can't combine 'r' and 'w' in mode.")
        self._storage = storage
        bucket, name = bucket_and_name(name)
        # self.name = name[len(self._storage.location) :].lstrip("/")
        self.name = name
        self._mode = mode
        self.obj = storage.bucket(bucket).Object(name)
        if "w" not in mode:
            # Force early RAII-style exception if object does not exist
            params = s3._filter_download_params(
                self._storage.get_object_parameters(self.name)
            )
            self.obj.load(**params)
        self._closed = False
        self._file = None
        self._parts = None
        # 5 MB is the minimum part size (if there is more than one part).
        # Amazon allows up to 10,000 parts.  The default supports uploads
        # up to roughly 50 GB.  Increase the part size to accommodate
        # for files larger than this.
        self.buffer_size = buffer_size or setting("AWS_S3_FILE_BUFFER_SIZE", 5242880)
        self._reset_file_properties()


@deconstructible
class S3Storage(s3.S3Storage):
    """
    Extends storages.backends.s3.S3torage to support files across buckets
    """

    def bucket(self, name):
        """
        Get a bucket by name.
        """
        return self.connection.Bucket(name)

    def _normalize_name(self, name):
        """
        Normalizes the name so that paths like /path/to/ignored/../something.txt
        work. We check to make sure that the path pointed to is not outside
        the directory specified by the LOCATION setting.
        """
        try:
            return name
        except ValueError:
            raise SuspiciousOperation("Attempted access to '%s' denied." % name)
    
    def _open(self, name, mode="rb"):
        name = self._normalize_name(clean_name(name))
        try:
            f = S3File(name, mode, self)
        except ClientError as err:
            if err.response["ResponseMetadata"]["HTTPStatusCode"] == 404:
                raise FileNotFoundError("File does not exist: %s" % name)
            raise  # Let it bubble up if it was some other error
        return f

    def _save(self, name, content):
        bucket, name = bucket_and_name(name)
        cleaned_name = clean_name(name)
        name = self._normalize_name(cleaned_name)
        params = self._get_write_parameters(name, content)

        if is_seekable(content):
            content.seek(0, os.SEEK_SET)

        # wrap content so read() always returns bytes. This is required for passing it
        # to obj.upload_fileobj() or self._compress_content()
        content = ReadBytesWrapper(content)

        if (
            self.gzip
            and params["ContentType"] in self.gzip_content_types
            and "ContentEncoding" not in params
        ):
            content = self._compress_content(content)
            params["ContentEncoding"] = "gzip"

        obj = self.bucket(bucket).Object(name)

        # Workaround file being closed errantly see: https://github.com/boto/s3transfer/issues/80
        original_close = content.close
        content.close = lambda: None
        try:
            obj.upload_fileobj(content, ExtraArgs=params, Config=self.transfer_config)
        finally:
            content.close = original_close
        return cleaned_name

    def delete(self, name):
        try:
            bucket, name = bucket_and_name(name)
            name = self._normalize_name(clean_name(name))
            self.bucket(bucket).Object(name).delete()
        except ClientError as err:
            if err.response["ResponseMetadata"]["HTTPStatusCode"] == 404:
                # Not an error to delete something that does not exist
                return

            # Some other error was encountered. Re-raise it
            raise

    def exists(self, name):
        bucket, name = bucket_and_name(name)
        name = self._normalize_name(clean_name(name))
        try:
            self.connection.meta.client.head_object(Bucket=bucket, Key=name)
            return True
        except ClientError as err:
            if err.response["ResponseMetadata"]["HTTPStatusCode"] == 404:
                return False

            # Some other error was encountered. Re-raise it.
            raise

    def listdir(self, name):
        bucket, name = bucket_and_name(name)
        path = self._normalize_name(clean_name(name))
        # The path needs to end with a slash, but if the root is empty, leave it.
        if path and not path.endswith("/"):
            path += "/"

        directories = []
        files = []
        file_sizes = []
        paginator = self.connection.meta.client.get_paginator("list_objects")
        pages = paginator.paginate(Bucket=bucket, Delimiter="/", Prefix=path)
        for page in pages:
            directories += [
                posixpath.relpath(entry["Prefix"], path)
                for entry in page.get("CommonPrefixes", ())
            ]
            for entry in page.get("Contents", ()):
                key = entry["Key"]
                if key != path:
                    files.append(posixpath.relpath(key, path))
                    file_sizes.append(entry["Size"])
        return directories, files, file_sizes

    def size(self, name):
        bucket, name = bucket_and_name(name)
        name = self._normalize_name(clean_name(name))
        try:
            return self.bucket(bucket).Object(name).content_length
        except ClientError as err:
            if err.response["ResponseMetadata"]["HTTPStatusCode"] == 404:
                raise FileNotFoundError("File does not exist: %s" % name)
            raise  # Let it bubble up if it was some other error

    def get_modified_time(self, name):
        """
        Returns an (aware) datetime object containing the last modified time if
        USE_TZ is True, otherwise returns a naive datetime in the local timezone.
        """
        bucket, name = bucket_and_name(name)
        name = self._normalize_name(clean_name(name))
        entry = self.bucket(bucket).Object(name)
        if setting("USE_TZ"):
            # boto3 returns TZ aware timestamps
            return entry.last_modified
        else:
            return make_naive(entry.last_modified)

    def url(self, name, parameters=None, expire=None, http_method=None):
        # Preserve the trailing slash after normalizing the path.

        bucket, name = bucket_and_name(name)
        name = self._normalize_name(clean_name(name))
        params = parameters.copy() if parameters else {}
        if expire is None:
            expire = self.querystring_expire

        if self.custom_domain:
            url = "{}//{}/{}{}".format(
                self.url_protocol,
                self.custom_domain,
                filepath_to_uri(name),
                "?{}".format(urlencode(params)) if params else "",
            )

            if self.querystring_auth and self.cloudfront_signer:
                expiration = datetime.utcnow() + timedelta(seconds=expire)
                return self.cloudfront_signer.generate_presigned_url(
                    url, date_less_than=expiration
                )

            return url

        params["Bucket"] = bucket
        params["Key"] = name

        connection = (
            self.connection if self.querystring_auth else self.unsigned_connection
        )
        url = connection.meta.client.generate_presigned_url(
            "get_object", Params=params, ExpiresIn=expire, HttpMethod=http_method
        )
        return url
