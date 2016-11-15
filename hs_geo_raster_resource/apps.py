from django.apps import AppConfig


class GeoRasterAppConfig(AppConfig):
    name = "hs_geo_raster_resource"

    def ready(self):
        import receivers  # noqa