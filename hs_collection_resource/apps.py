from django.apps import AppConfig


class CollectionResourceAppConfig(AppConfig):
    name = "hs_collection_resource"

    def ready(self):
        from . import receivers  # noqa
