"""Simple App configuration for hs_core module."""

from django.apps import AppConfig


class HSCoreAppConfig(AppConfig):
    """Configures options for hs_core app."""

    name = "hs_core"

    def ready(self):
        """On application ready, import receivers for Django signals."""
        import receivers  # noqa
