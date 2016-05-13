from __future__ import unicode_literals

import os
import shutil
import logging
import tempfile

from django.db import migrations
from django.core.files.uploadedfile import UploadedFile

from django_irods.storage import IrodsStorage
from hs_core import hydroshare
from hs_core.hydroshare.utils import resource_modified
from hs_geo_raster_resource.models import RasterResource
from hs_geo_raster_resource.receivers import create_vrt_file
from hs_geo_raster_resource import raster_meta_extract


def migrate_tif_file(apps, schema_editor):
    log = logging.getLogger()
    success = 0
    fail = []
    not_modify = []

    for res in RasterResource.objects.all():
        if res.files.all():
            try:
                # copy all the files of a resource to temp dir
                temp_dir = tempfile.mkdtemp()
                for res_file in res.files.all():
                    shutil.copy(res_file.resource_file.file.name,
                                os.path.join(temp_dir, os.path.basename(res_file.resource_file.name)))

                # metadata extraction from temp dir
                ori_dir = os.getcwd()
                os.chdir(temp_dir)
                vrt_file_path = [os.path.join(temp_dir, f) for f in os.listdir(temp_dir) if '.vrt' == os.path.splitext(f)[1]].pop()
                res_md_dict = raster_meta_extract.get_raster_meta_dict(vrt_file_path)
                os.chdir(ori_dir)
                shutil.rmtree(temp_dir)

                # update band metadata of raster resources
                is_modified = False
                if res_md_dict['band_info']:
                    for i, band_meta in res_md_dict['band_info'].items():
                        band_obj = res.metadata.bandInformation.filter(name='Band_{}'.format(str(i))).first()
                        if band_obj:
                            res.metadata.update_element('bandInformation',
                                                        band_obj.id,
                                                        maximumValue=band_meta['maximumValue'],
                                                        minimumValue=band_meta['minimumValue'],
                                                        noDataValue=band_meta['noDataValue'],
                                                        )
                            is_modified = True

                # resource modify update
                if is_modified:
                    resource_modified(res, res.creator)
                    success += 1
                    log.info('Raster metadata is updated successfully for resource:ID:{} '
                             'Title:{}'.format(res.short_id, res.metadata.title.value))
                else:
                    log.info('Raster metadata is not updated for resource:ID:{} '
                             'Title:{}'.format(res.short_id, res.metadata.title.value))
                    not_modify.append({res.short_id: res.metadata.title.value})

            except Exception as e:
                fail.append({res.short_id : res.metadata.title.value})
                log.info('Raster metadata update failed for resource:ID:{} '
                        'Title:{}'.format(res.short_id, res.metadata.title.value))

    print 'total resources: {}'.format(str(RasterResource.objects.all().count()))  # 16:44 start
    print 'success update resources: {}'.format(str(success))
    print 'failed update resources: {}'.format(str(fail))
    print 'not updated resources: {}'.format(str(not_modify))


def undo_migrate_tif_file(apps, schema_editor):

    # loop through all the band information and change the nodata value, min, max values as none
    for res in RasterResource.objects.all():
        try:
            for band_obj in res.metadata.bandInformation:
                res.metadata.update_element('bandInformation',
                                            band_obj.id,
                                            maximumValue=None,
                                            minimumValue=None,
                                            noDataValue=None,
                                            )
        except:
            pass


class Migration(migrations.Migration):

    dependencies = [
        ('hs_geo_raster_resource', '0005_auto_20160509_2116'),
    ]

    operations = [
        migrations.RunPython(code=migrate_tif_file, reverse_code=undo_migrate_tif_file),
    ]
