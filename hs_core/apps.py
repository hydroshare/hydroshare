"""Simple App configuration for hs_core module."""

from django.apps import AppConfig
from health_check.plugins import plugin_dir


class HSCoreAppConfig(AppConfig):
    """Configures options for hs_core app."""

    name = "hs_core"

    def ready(self):
        """On application ready, import receivers for Django signals."""
        from . import receivers  # noqa

        from hydroshare.health_check import PeriodicTasksHealthCheck
        plugin_dir.register(PeriodicTasksHealthCheck)
