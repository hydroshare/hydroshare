from django.apps import AppConfig


class MODFLOWModelInstanceAppConfig(AppConfig):
    name = "hs_modflow_modelinstance"

    def ready(self):
        from . import receivers  # noqa
