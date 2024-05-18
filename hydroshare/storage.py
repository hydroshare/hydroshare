from storages.backends.gcloud import GoogleCloudStorage
from django.contrib.staticfiles.storage import ManifestFilesMixin, ManifestStaticFilesStorage
import logging


class ForgivingManifestStaticFilesStorage(ManifestStaticFilesStorage):
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


class ManifestGoogleCloudStorage(ManifestFilesMixin, GoogleCloudStorage):
    logger = logging.getLogger('django.contrib.staticfiles')

    # TODO: remove this function
    # def _save(self, name, content):
    #     try:
    #         return super()._save(name, content)
    #     except Exception as ex:
    #         # When the file is missing, let's forgive and ignore that.
    #         msg = f"Exception for file: {name} during save. \nError: {str(ex)}"
    #         print(msg)
    #         self.logger.warning(msg)
    #         return name

    def hashed_name(self, name, content=None, filename=None):
        try:
            result = super(ManifestGoogleCloudStorage).hashed_name(name, content, filename)
        except ValueError as ex:
            # When the file is missing, let's forgive and ignore that.
            msg = f"Ignoring ValueError for missing file: {name}, during static collection. \nError: {str(ex)}"
            print(msg)
            self.logger.warning(msg)
            result = name
        return result

    def path(self, name):
        # https://github.com/jschneier/django-storages/issues/1149
        # https://github.com/jschneier/django-storages/issues/1149
        return name

    # TODO: test with collectstatic to make sure it works


def Static():
    return ManifestGoogleCloudStorage(location='static')
