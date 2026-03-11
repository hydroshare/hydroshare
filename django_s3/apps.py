from django.apps import AppConfig


class DjangoS3AppConfig(AppConfig):
    name = "django_s3"

    def ready(self):
        from .storage import S3Storage
        istorage = S3Storage()
        if not istorage.bucket_exists('bags'):
            istorage.connection.create_bucket(Bucket='bags')
        if not istorage.bucket_exists('zips'):
            istorage.connection.create_bucket(Bucket='zips')
        if not istorage.bucket_exists('tmp'):
            istorage.connection.create_bucket(Bucket='tmp')
