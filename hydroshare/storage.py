from django.contrib.staticfiles.storage import ManifestStaticFilesStorage
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
