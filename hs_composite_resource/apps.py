from django.apps import AppConfig


class CompositeResourceAppConfig(AppConfig):
    name = "hs_composite_resource"

    def ready(self):
        from . import receivers  # noqa
