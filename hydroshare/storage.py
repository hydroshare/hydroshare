import os
from django.conf import settings
from django.contrib.staticfiles.storage import ManifestStaticFilesStorage


class CustomManifestStaticFilesStorage(ManifestStaticFilesStorage):
    def hashed_name(self, name, content=None, filename=None):
        try:
            return super().hashed_name(name, content, filename)
        except ValueError:
            return name