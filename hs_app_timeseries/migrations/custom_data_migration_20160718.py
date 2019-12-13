import logging

from django.db import migrations

from hs_core.hydroshare.utils import resource_modified


def delete_extracted_metadata(apps, schema_editor):
    # For all existing timeseries resources, delete all resource specific metadata.
    # This way we can keep the resource GUID and allow the resource owners to manually
    # delete the existing SQlite file and then add a new SQlite file to regenerate
    # resource specific metadata
    log = logging.getLogger()

    # Trying to delete resource specific metadata by accessing these objects
    # from a resource object (e.g res.metadata.sites.delete() randomly raises attribute
    # error for 'metadata' property of resource object. Need to delete the objects directly.
    Site = apps.get_model('hs_app_timeseries', 'Site')
    Variable = apps.get_model('hs_app_timeseries', 'Variable')
    Method = apps.get_model('hs_app_timeseries', 'Method')
    ProcessingLevel = apps.get_model('hs_app_timeseries', 'ProcessingLevel')
    TimeSeriesResult = apps.get_model('hs_app_timeseries', 'TimeSeriesResult')

    # delete timeseries specific metadata elements
    Site.objects.all().delete()
    Variable.objects.all().delete()
    Method.objects.all().delete()
    ProcessingLevel.objects.all().delete()
    TimeSeriesResult.objects.all().delete()
    log.info("Deleted all resource specific metadata for all timeseries resources.")
    print("Deleted all resource specific metadata for all timeseries resources.")


class Migration(migrations.Migration):

    dependencies = [
        ('hs_app_timeseries', '0005_auto_20160713_1905'),
    ]

    operations = [
        migrations.RunPython(code=delete_extracted_metadata),
    ]