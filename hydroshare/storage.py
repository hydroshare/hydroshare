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
            msg = f"Ignoring ValueError: {str(ex)}"
            print(msg)
            self.logger.warning(msg)
            result = name
        return result


class ForgivingManifestStaticFilesStorage(ForgivingManifestFilesMixin, ManifestStaticFilesStorage):

    # https://docs.djangoproject.com/en/4.2/ref/contrib/staticfiles/#django.contrib.staticfiles.storage.ManifestStaticFilesStorage
    support_js_module_import_aggregation = True


class ManifestGoogleCloudStorage(ForgivingManifestFilesMixin, GoogleCloudStorage):
    support_js_module_import_aggregation = True
    logger = logging.getLogger('django.contrib.staticfiles')

    @property
    def local_manifest_path(self):
        """Always return the current local manifest path"""
        return os.path.join(settings.PROJECT_ROOT, self.manifest_name)

    def path(self, name):
        return name

    def read_manifest(self):
        """
        Looks up staticfiles.json in Project directory (local filesystem)
        """
        self.logger.info(f"Reading manifest from {self.local_manifest_path}")
        try:
            with open(self.local_manifest_path, 'r') as manifest:
                return manifest.read()
        except (IOError, FileNotFoundError):
            return None

    def save_manifest(self):
        """
        Save the manifest to local filesystem instead of cloud storage
        """
        self.logger.info(f"Saving manifest to {self.local_manifest_path}")
        # Ensure the directory exists
        os.makedirs(settings.PROJECT_ROOT, exist_ok=True)

        # Calculate manifest hash
        self.manifest_hash = self.file_hash(
            None, ContentFile(json.dumps(sorted(self.hashed_files.items())).encode())
        )

        # Prepare payload
        payload = {
            "paths": self.hashed_files,
            "version": self.manifest_version,
            "hash": self.manifest_hash,
        }

        # Save to local filesystem
        contents = json.dumps(payload, indent=2)
        try:
            with open(self.local_manifest_path, 'w') as manifest_file:
                manifest_file.write(contents)
        except IOError as e:
            self.logger.error(
                f"Error saving manifest file: {e}"
            )
            raise


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
