from django.apps import AppConfig


class SWATModelInstanceAppConfig(AppConfig):
    name = "hs_swat_modelinstance"

    def ready(self):
        from . import receivers  # noqa
