from __future__ import unicode_literals

import os
import shutil
import logging
import tempfile
import subprocess
import xml.etree.ElementTree as ET

from django.db import migrations
from django.core.files.uploadedfile import UploadedFile

from django_irods.storage import IrodsStorage
from hs_core import hydroshare
from hs_core.hydroshare.utils import resource_modified
from hs_geo_raster_resource.models import RasterResource
from hs_geo_raster_resource import raster_meta_extract


def migrate_tif_file(apps, schema_editor):
    log = logging.getLogger()
    istorage = IrodsStorage()

    copy_res_fail = []
    meta_update_fail = []
    meta_update_success = []

    # start migration for each raster resource that has raster files
    for res in RasterResource.objects.all():
        if res.files.all():
            # copy all the resource files to temp dir
            try:
                temp_dir = tempfile.mkdtemp()
                for res_file in res.files.all():
                    shutil.copy(res_file.resource_file.file.name,
                                os.path.join(temp_dir, os.path.basename(res_file.resource_file.name)))

                vrt_file_path = [os.path.join(temp_dir, f) for f in os.listdir(temp_dir) if '.vrt' == f[-4:]].pop()

            except Exception as e:
                log.exception(e.message)
                copy_res_fail.append('{}:{}'.format(res.short_id, res.metadata.title.value))
                continue

            # update the metadata for the original coverage information of all the raster resources
            try:
                meta_updated = False

                # extract meta
                ori_dir = os.getcwd()
                os.chdir(temp_dir)
                res_md_dict = raster_meta_extract.get_raster_meta_dict(vrt_file_path)
                os.chdir(ori_dir)
                shutil.rmtree(temp_dir)

                # update original coverage information for datum and coordinate string in django
                if res.metadata.originalCoverage:
                    original_value = res.metadata.originalCoverage.value
                    res.metadata.originalCoverage.delete()
                    if res_md_dict['spatial_coverage_info']['original_coverage_info']['datum']:
                        v = {'value': res_md_dict['spatial_coverage_info']['original_coverage_info']}
                        res.metadata.create_element('OriginalCoverage', **v)
                        meta_updated = True

                # update the bag if meta is updated
                if meta_updated:
                    bag_name = 'bags/{res_id}.zip'.format(res_id=res.short_id)
                    if istorage.exists(bag_name):
                        # delete the resource bag as the old bag is not valid
                        istorage.delete(bag_name)
                    resource_modified(res, res.creator)
                    meta_update_success.append('{}:{}'.format(res.short_id, res.metadata.title.value))

            except Exception as e:
                log.exception(e.message)
                if original_value:
                    v = {'value': original_value}
                    res.metadata.create_element('OriginalCoverage', **v)
                meta_update_fail.append('{}:{}'.format(res.short_id, res.metadata.title.value))

    # Print migration results
    print 'Copy resource to temp folder failure: Number: {} List: {}'.format(len(copy_res_fail), copy_res_fail)
    print 'Meta update success: Number: {} List {}'.format(len(meta_update_success), meta_update_success)
    print 'Meta update fail: Number: {} List {}'.format(len(meta_update_fail), meta_update_fail)


def undo_migrate_tif_file(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('hs_geo_raster_resource', 'custom_migration_for_raster_meta_update_20160512'),
    ]

    operations = [
        migrations.RunPython(code=migrate_tif_file, reverse_code=undo_migrate_tif_file),
    ]
