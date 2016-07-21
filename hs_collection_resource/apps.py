from django.apps import AppConfig


class CollectionResourceAppConfig(AppConfig):
    name = "hs_collection_resource"

    def ready(self):
        import receivers
