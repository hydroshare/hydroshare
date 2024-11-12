from storages.backends.gcloud import GoogleCloudStorage
from django.contrib.staticfiles.storage import ManifestFilesMixin
import logging


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


class ManifestGoogleCloudStorage(ForgivingManifestFilesMixin, GoogleCloudStorage):

    support_js_module_import_aggregation = True

    def path(self, name):
        # https://docs.djangoproject.com/en/3.2/ref/files/storage/#django.core.files.storage.Storage.path
        # https://github.com/jschneier/django-storages/issues/1149
        # The path() method is not implemented for GoogleCloudStorage.
        # The storage backend does not have a local filesystem path.
        # Here we avoid https://docs.python.org/3/library/exceptions.html#NotImplementedError by returning the name.
        return name


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
