"""
This command will update all GeoServer data services.

This will loop through all public composite resources
containing geographic feature, geographic raster, and/or
time series content and send an update signal to the Web
Services Manager application. Web services must be enabled
in local_settings.py.
"""

from django.core.management.base import BaseCommand
from hs_core.models import BaseResource
from django.conf import settings
from hs_core.tasks import update_web_services


class Command(BaseCommand):
    help = "Updates web services for all public resources."

    def add_arguments(self, parser):
        # A list of resource ID's, or None to check all resources.
        parser.add_argument("resource_ids", nargs="*", type=str)

    def handle(self, *args, **options):
        # Run only if web services are enabled.
        if settings.HSWS_ACTIVATED:
            # Get a list of public resources, or specified public resources.
            if len(options["resource_ids"]) > 0:
                resource_list = [BaseResource.public_resources.get(
                    short_id=resource_id
                ) for i in options["resource_ids"]]
            else:
                resource_list = BaseResource.public_resources.all()
            # Update composite resources containing geospatial content.
            for resource in resource_list:
                if resource.discovery_content_type == "Composite":
                    res_logical_file_types = [
                        logical_file.get_aggregation_type_name()
                        for logical_file in resource.logical_files
                    ]
                    if any(i in res_logical_file_types for i in [
                        "GeographicRasterAggregation",
                        "GeographicFeatureAggregation",
                        "TimeSeriesAggregation"
                    ]):
                        update_web_services.apply_async((
                            settings.HSWS_URL,
                            settings.HSWS_API_TOKEN,
                            settings.HSWS_TIMEOUT,
                            settings.HSWS_PUBLISH_URLS,
                            resource.short_id
                        ), countdown=1)
