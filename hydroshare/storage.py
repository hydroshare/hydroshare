from django.contrib.staticfiles.storage import ManifestStaticFilesStorage
import logging
from urllib.parse import unquote, urlsplit, urlunsplit


class ForgivingManifestStaticFilesStorage(ManifestStaticFilesStorage):
    """
    Allow collectstatic to continue even if files are missing
    """
    logger = logging.getLogger('django.contrib.staticfiles')

    # Ideally, just setting manifest_strict would solve this issue but there is a known issue:
    # https://code.djangoproject.com/ticket/31520
    # So overriding two of the functions
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

    # stored_name calls hashed_name so we shouldn't have to override it as well
    # def stored_name(self, name):
    #     try:
    #         result = super().stored_name(name)
    #     except ValueError as ex:
    #         # When the file is missing, let's forgive and ignore that.
    #         msg = f"Ignoring ValueError for missing file: {name}, during static collection. \nError: {str(ex)}"
    #         print(msg)
    #         self.logger.warning(msg)
    #         cache_name = self.clean_name(name)
    #         parsed_name = urlsplit(unquote(name))
    #         unparsed_name = list(parsed_name)
    #         unparsed_name[2] = cache_name
    #         if '?#' in name and not unparsed_name[3]:
    #             unparsed_name[2] += '?'
    #         result = urlunsplit(unparsed_name)
    #     return result