from django.apps import AppConfig


class HSTrackingAppConfig(AppConfig):
    name = 'hs_tracking'

    def ready(self):
        # Activate the signal handlers
        import hs_tracking.signals  # noqa
