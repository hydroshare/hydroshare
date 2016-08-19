from django.apps import AppConfig


class HSCoreAppConfig(AppConfig):
    name = "hs_core"

    def ready(self):
        import receivers
