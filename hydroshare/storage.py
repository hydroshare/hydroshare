from storages.backends.gcloud import GoogleCloudStorage
from django.contrib.staticfiles.storage import ManifestFilesMixin, ManifestStaticFilesStorage
import logging
import os
import json
from django.conf import settings
from django.core.files.base import ContentFile


class ForgivingManifestFilesMixin(ManifestFilesMixin):
    """
    Allow collectstatic to continue even if files are missing
    """
    logger = logging.getLogger('django.contrib.staticfiles')

    # Ideally, just setting manifest_strict would solve this issue but there is a known issue:
    # https://code.djangoproject.com/ticket/31520
    # So overriding one of the functions
    # stored_name calls hashed_name so we don't have to override it as well
    manifest_strict = False

    def hashed_name(self, name, content=None, filename=None):
        try:
            result = super().hashed_name(name, content, filename)
        except ValueError as ex:
            # When the file is missing, let's forgive and ignore that.
            msg = f"Ignoring ValueError for missing file: {name}, during static collection. \nError: {str(ex)}"
            print(msg)
            self.logger.warning(msg)
            result = name
        return result


class ForgivingManifestStaticFilesStorage(ForgivingManifestFilesMixin, ManifestStaticFilesStorage):

    # https://docs.djangoproject.com/en/4.2/ref/contrib/staticfiles/#django.contrib.staticfiles.storage.ManifestStaticFilesStorage
    support_js_module_import_aggregation = True


class ManifestGoogleCloudStorage(ForgivingManifestFilesMixin, GoogleCloudStorage):
    support_js_module_import_aggregation = True

    def path(self, name):
        # https://docs.djangoproject.com/en/3.2/ref/files/storage/#django.core.files.storage.Storage.path
        # https://github.com/jschneier/django-storages/issues/1149
        # The path() method is not implemented for GoogleCloudStorage.
        # The storage backend does not have a local filesystem path.
        # Here we avoid https://docs.python.org/3/library/exceptions.html#NotImplementedError by returning the name.
        return name

    def read_manifest(self):
        """
        Looks up staticfiles.json in Project directory
        """
        manifest_location = os.path.abspath(
            os.path.join(settings.PROJECT_ROOT, self.manifest_name)
        )
        try:
            with open(manifest_location) as manifest:
                return manifest.read().decode('utf-8')
        except IOError:
            return None

    def save_manifest(self):
        self.manifest_hash = self.file_hash(
            None, ContentFile(json.dumps(sorted(self.hashed_files.items())).encode())
        )
        payload = {
            "paths": self.hashed_files,
            "version": self.manifest_version,
            "hash": self.manifest_hash,
        }
        if self.manifest_storage.exists(self.manifest_name):
            self.manifest_storage.delete(self.manifest_name)
        contents = json.dumps(payload).encode()
        self.manifest_storage._save(self.manifest_name, ContentFile(contents))


class MediaGoogleCloudStorage(GoogleCloudStorage):
    '''
    Google Cloud Storage backend for Django static files. Implements methods the
    mezzanine admin interface requires.
    '''

    def isfile(self, name):
        return self.exists(name)

    def isdir(self, name):
        if not name:  # Empty name is a directory
            return True

        return self.isfile(name)

    def makedirs(self, name):
        pass


def Static():
    return ManifestGoogleCloudStorage(location='static')
