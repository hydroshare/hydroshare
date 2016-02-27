from __future__ import unicode_literals

import os
import shutil
import logging

from django.db import migrations
from django.core.files.uploadedfile import UploadedFile


from hs_core import hydroshare
from hs_geo_raster_resource.models import RasterResource
from hs_geo_raster_resource.receivers import create_vrt_file


def migrate_tif_file(apps, schema_editor):
    # create a vrt file from tif file for each of the Raster Resources
    log = logging.getLogger()
    for res in RasterResource.objects.all():

        res_file = res.files.all().first()
        vrt_file_path, temp_dir = create_vrt_file(res_file.resource_file)
        if os.path.isfile(vrt_file_path):
            files = (UploadedFile(file=open(vrt_file_path, 'r'), name=os.path.basename(vrt_file_path)))
            hydroshare.add_resource_files(res.short_id, files)
            print 'Tif file conversion to VRT successful for resource:ID:{} Title:{}'.format(res.short_id, res.metadata.title.value)
            log.info('Tif file conversion to VRT successful for resource:ID:{} '
                     'Title:{}'.format(res.short_id, res.metadata.title.value))
        else:
            print 'Tif file conversion to VRT unsuccessful for resource:ID:{} Title:{}'.format(res.short_id, res.metadata.title.value)
            log.error('Tif file conversion to VRT unsuccessful for resource:ID:{} '
                      'Title:{}'.format(res.short_id, res.metadata.title.value))
        if os.path.isdir(temp_dir):
            shutil.rmtree(temp_dir)


def undo_migrate_tif_file(apps, schema_editor):
    # delete vrt file from each of the raster resources
    for res in RasterResource.objects.all():
        for res_file in res.files.all():
            file_ext = os.path.splitext(res_file.resource_file.name)[1]
            if file_ext == '.vrt':
                file_name = os.path.basename(res_file.resource_file.name)
                hydroshare.delete_resource_file(res.short_id, file_name, res.creator)


class Migration(migrations.Migration):

    dependencies = [
        ('hs_geo_raster_resource', '0004_auto_20151116_2257'),
    ]

    operations = [
        migrations.RunPython(code=migrate_tif_file, reverse_code=undo_migrate_tif_file),
    ]
