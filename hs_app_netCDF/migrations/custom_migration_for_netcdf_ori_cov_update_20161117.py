from __future__ import unicode_literals

import logging

from django.db import migrations

from hs_core.hydroshare.utils import resource_modified
from hs_app_netCDF.models import NetcdfResource


def migrate_nc_file(apps, schema_editor):
    log = logging.getLogger()
    meta_update_fail = []
    meta_update_success = []

    for res in NetcdfResource.objects.all():
        try:
            resource_modified(res, res.creator)
            meta_update_success.append(
                '{}:{}'.format(res.short_id, res.metadata.title.value))

        except Exception as e:
            log.exception(e.message)
            meta_update_fail.append('{}:{}'.format(res.short_id, res.metadata.title.value))

    print 'Meta update success: Number: {} List {}'.format(len(meta_update_success),
                                                           meta_update_success)
    print 'Meta update fail: Number: {} List {}'.format(len(meta_update_fail), meta_update_fail)


def undo_migrate_nc_file(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('hs_app_netCDF', '0005_auto_20161111_2322'),
    ]

    operations = [
        migrations.RunPython(code=migrate_nc_file, reverse_code=undo_migrate_nc_file),
    ]