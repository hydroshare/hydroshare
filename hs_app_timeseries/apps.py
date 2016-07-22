from django.apps import AppConfig


class TimeSeriesAppConfig(AppConfig):
    name = "hs_app_timeseries"

    def ready(self):
        import receivers