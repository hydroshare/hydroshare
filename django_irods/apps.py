from django.apps import AppConfig


class CompositeResourceAppConfig(AppConfig):
    name = "django_irods"

    def ready(self):
        from .storage import IrodsStorage
        istorage = IrodsStorage()
        istorage.create_bucket('bags')
        istorage.create_bucket('zips')
        istorage.create_bucket('tmp')
