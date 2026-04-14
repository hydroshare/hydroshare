from django.apps import AppConfig


class DjangoS3AppConfig(AppConfig):
    name = "django_s3"

    def ready(self):
        from .storage import S3Storage
        istorage = S3Storage()
        # TODO, this is only for local development.
        # The bucket should already exist and this will likely be moved to the setup script.
        if not istorage.bucket_exists('hydroshare'):
            istorage.connection.create_bucket(Bucket='hydroshare')
