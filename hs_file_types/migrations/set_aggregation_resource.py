import logging

from django.db import migrations


def set_aggregation_resource(apps, schema_editor):
    CompositeResource = apps.get_model('hs_composite_resource', 'CompositeResource')
    """Sets the new resource attribute of the aggregation object
    for each of the aggregations in each of the existing composite resources
    """

    log = logging.getLogger()
    count = 0
    for res in CompositeResource.objects.all():
        for file in res.files.all():
            if file.has_logical_file:
                log.info("Setting resource attribute as {} for file {}".format(res.short_id, str(file)))
                file.logical_file.resource = res
                file.logical_file.save()
                count = count + 1

    log_msg = "A total of {} logical files were processed.".format(count)
    log.info(log_msg)


class Migration(migrations.Migration):

    dependencies = [
        ('hs_file_types', '0009_auto_20181028_1554'),
    ]

    operations = [
        migrations.RunPython(code=set_aggregation_resource),
    ]
