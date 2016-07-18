import logging

from django.db import migrations

from hs_core.hydroshare.utils import resource_modified
from hs_app_timeseries.models import TimeSeriesResource


def delete_extracted_metadata(apps, schema_editor):
    # For all existing timeseries resources, delete all resource specific metadata.
    # This way we can keep the resource GUID and allow the resource owners to manually
    # delete the existing SQlite file and then add a new SQlite file to regenerate
    # resource specific metadata
    log = logging.getLogger()
    for res in TimeSeriesResource.objects.all():
        # delete all extracted metadata
        res.metadata.sites.delete()
        res.metadata.variables.delete()
        res.metadata.methods.delete()
        res.metadata.processing_levels.delete()
        res.metadata.time_series_results.delete()
        message = "Deleted all resource specific metadata from TimeSeries Resource ID:{}"
        message = message.format(res.short_id)
        log.info(message)
        print(message)
        resource_modified(res, res.creator)


class Migration(migrations.Migration):

    dependencies = [
        ('hs_app_timeseries', '0005_auto_20160713_1905'),
    ]

    operations = [
        migrations.RunPython(code=delete_extracted_metadata),
    ]