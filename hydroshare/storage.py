from django.contrib.staticfiles.storage import ManifestStaticFilesStorage
import logging


class ForgivingManifestStaticFilesStorage(ManifestStaticFilesStorage):
    """
    Allow collectstatic to continue even if files are missing for 3rd party libraries
    Later versions of django have a 'manifest_strict' parameter that would allow this:
    https://docs.djangoproject.com/en/4.0/ref/contrib/staticfiles/#django.contrib.staticfiles.storage.ManifestStaticFilesStorage.manifest_strict
    """
    logger = logging.getLogger()

    def hashed_name(self, name, content=None, filename=None):
        try:
            result = super().hashed_name(name, content, filename)
        except ValueError as ex:
            # When the file is missing, let's forgive and ignore that.
            msg = f"Ignoring ValueError for missing file: {name}, during static collection. Error: {str(ex)}"
            self.logger.warning(msg)
            result = name
        return result
