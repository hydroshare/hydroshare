from django.apps import AppConfig


class ToolsResourceAppConfig(AppConfig):
    name = "hs_tools_resource"
    verbose_name = "Applications"

    def ready(self):
        import receivers  # noqa
