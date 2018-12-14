import logging

from django.db import migrations


def get_aggregations(resource):
    lf_list = []
    if resource.has_files():
        for file in resource.files.all():
            if file.has_logical_file:
                if not hasattr(file.logical_file, 'resource'):
                    lf_list.append(file.logical_file)

    return lf_list


def set_aggregation_resource(apps, schema_editor):
    """Sets the new resource attribute of the aggregation object
    for each of the aggregations in each of the existing composite resources
    """

    log = logging.getLogger()
    CompositeResource = apps.get_model("hs_composite_resource", "CompositeResource")

    log_msg_1 = "All aggregations (total of {aggr_count}) for resource (ID:{res_id}) were " \
                "successfully assigned the resource object."
    log_msg_2 = "There are no aggregations in resource (ID:{})."
    for res in CompositeResource.objects.all():
        res_aggregations = get_aggregations(res)
        for aggregation in res_aggregations:
            aggregation.resource = res
            aggregation.save()
        if res_aggregations:
            log_msg = log_msg_1.format(aggr_count=len(res_aggregations), res_id=res.short_id)
            if __debug__:
                log.debug(log_msg)
            log.info(log_msg)
        else:
            log_msg = log_msg_2.format(res.short_id)
            if __debug__:
                log.debug(log_msg)
            log.info(log_msg)

    log_msg = "A total of {} composite resources were processed.".format(
        CompositeResource.objects.all().count())
    if __debug__:
        log.debug(log_msg)
    log.info(log_msg)


class Migration(migrations.Migration):

    dependencies = [
        ('hs_file_types', '0009_auto_20181028_1554'),
    ]

    operations = [
        migrations.RunPython(code=set_aggregation_resource),
    ]
