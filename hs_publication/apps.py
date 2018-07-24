from django.apps import AppConfig


class PublicationAppConfig(AppConfig):
    name = "hs_publication"
    verbose_name = "DOI Publication"

    def ready(self):
        pass
