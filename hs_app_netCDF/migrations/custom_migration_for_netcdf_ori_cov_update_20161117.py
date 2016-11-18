from __future__ import unicode_literals

import os
import shutil
import logging

from django.db import migrations

from hs_core.hydroshare.utils import resource_modified, get_file_from_irods
from hs_app_netCDF.models import NetcdfResource
from hs_app_netCDF.nc_functions.nc_meta import get_nc_meta_dict


def migrate_nc_file(apps, schema_editor):
    log = logging.getLogger()
    meta_update_fail = []
    meta_update_success = []

    # start migration for each raster resource that has raster files
    for res in NetcdfResource.objects.all():
        res_file_tmp_path = ''

        try:
            # get netCDF file path
            for res_file in res.files.all():
                res_file_tmp_path = get_file_from_irods(res_file)
                if os.path.splitext(res_file_tmp_path)[1] == '.nc':
                    break
                else:
                    shutil.rmtree(res_file_tmp_path)

            # extract metadata
            if os.path.isfile(res_file_tmp_path):
                res_md_dict = get_nc_meta_dict(res_file_tmp_path)
                res_dublin_core_meta = res_md_dict['dublin_core_meta']
                shutil.rmtree(res_file_tmp_path)

                # update the original spatial coverage meta
                if res_dublin_core_meta.get('original-box'):
                    # res.metadata.ori_coverage.all().delete()
                    # if res_dublin_core_meta.get('projection-info'):
                    #
                    #     res.metadata.create_element(
                    #         'originalcoverage',
                    #         value=res_dublin_core_meta['original-box'],
                    #         projection_string_type=res_dublin_core_meta['projection-info']['type'],
                    #         projection_string_text=res_dublin_core_meta['projection-info']['text'],
                    #         datum=res_dublin_core_meta['projection-info']['datum'])
                    # else:
                    #     res.metadata.create_element(
                    #         'originalcoverage',
                    #         value=res_dublin_core_meta['original-box'])

                    # update the resource status
                    resource_modified(res, res.creator)
                    meta_update_success.append(
                        '{}:{}'.format(res.short_id, res.metadata.title.value))

        except Exception as e:
            if os.path.isfile(res_file_tmp_path):
                shutil.rmtree(os.path.dirname(res_file_tmp_path))
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