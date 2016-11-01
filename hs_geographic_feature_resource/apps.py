from django.apps import AppConfig


class GeographicFeatureResourceAppConfig(AppConfig):
    name = "hs_geographic_feature_resource"

    def ready(self):
        import receivers
