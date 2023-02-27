from django.apps import AppConfig


class ExternalResourceAppConfig(AppConfig):
    name = "hs_external_resource"

    def ready(self):
        from . import receivers  # noqa
