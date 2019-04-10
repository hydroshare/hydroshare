from django.apps import AppConfig


class NetCDFAppConfig(AppConfig):
    name = "hs_app_netCDF"

    def ready(self):
        import receivers  # noqa
