"""Simple App configuration for hs_gabbs_web_app module."""

from django.apps import AppConfig


class HSGABBsAppConfig(AppConfig):
    """Configures options for hs_core app."""

    name = "hs_gabbs_web_app"

    def ready(self):
        """On application ready, import receivers for Django signals."""
        import hs_gabbs_web_app.receivers  # noqa
