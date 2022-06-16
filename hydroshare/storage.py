from django.contrib.staticfiles.storage import ManifestStaticFilesStorage


class ForgivingManifestStaticFilesStorage(ManifestStaticFilesStorage):
    """
    Allow collectstatic to continue even if files are missing
    """
    manifest_strict = False