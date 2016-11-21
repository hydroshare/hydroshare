from django.apps import AppConfig


class ToolsResourceAppConfig(AppConfig):
    name = "hs_tools_resource"

    def ready(self):
        import receivers  # noqa
