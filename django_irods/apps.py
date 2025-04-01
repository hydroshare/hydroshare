from django.apps import AppConfig


class DjangoS3AppConfig(AppConfig):
    name = "django_irods"

    def ready(self):
        from .storage import S3Storage
        istorage = S3Storage()
        istorage.create_bucket('bags')
        istorage.create_bucket('zips')
        istorage.create_bucket('tmp')
