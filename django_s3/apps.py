from django.apps import AppConfig

from hydroshare import settings


class DjangoS3AppConfig(AppConfig):
    name = "django_s3"

    def ready(self):
        from .storage import S3Storage
        istorage = S3Storage()
        istorage.create_bucket('bags')
        istorage.create_bucket('zips')
        istorage.create_bucket('tmp')
        if settings.DEBUG:
            istorage.create_bucket('hsmetadata')
