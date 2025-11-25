"""Simple App configuration for hs_core module."""

from django.apps import AppConfig
from health_check.plugins import plugin_dir


class HSCoreAppConfig(AppConfig):
    """Configures options for hs_core app."""

    name = "hs_core"

    def ready(self):
        """On application ready, import receivers for Django signals."""
        from . import receivers  # noqa
        from django.contrib.sites.models import Site
        from hs_core.mezzanine_patch import patched_site_get, patched_site_get_current

        # Save original methods FIRST
        if not hasattr(Site.objects, "get_original"):
            Site.objects.get_original = Site.objects.get

        # Apply patches (Site creation handled automatically in patch if needed)
        Site.objects.get = patched_site_get
        Site.objects.get_current = patched_site_get_current

        from hydroshare.health_check import PeriodicTasksHealthCheck
        plugin_dir.register(PeriodicTasksHealthCheck)
