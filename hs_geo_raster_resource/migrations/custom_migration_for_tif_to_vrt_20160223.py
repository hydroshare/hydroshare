from __future__ import unicode_literals

import os
import shutil
import logging

from django.db import migrations
from django.core.files.uploadedfile import UploadedFile

from django_irods.storage import IrodsStorage
from hs_core import hydroshare
from hs_core.hydroshare.utils import resource_modified
from hs_geo_raster_resource.models import RasterResource
from hs_file_types.models.raster import create_vrt_file


def migrate_tif_file(apps, schema_editor):
    # create a vrt file from tif file for each of the Raster Resources
    log = logging.getLogger()
    istorage = IrodsStorage()
    for res in RasterResource.objects.all():
        try:
            if len(res.files.all()) == 1:
                res_file = res.files.all().first()
                vrt_file_path = create_vrt_file(res_file.resource_file)
                if os.path.isfile(vrt_file_path):
                    files = (UploadedFile(file=open(vrt_file_path, 'r'),
                                          name=os.path.basename(vrt_file_path)))
                    hydroshare.add_resource_files(res.short_id, files)

                    bag_name = 'bags/{res_id}.zip'.format(res_id=res.short_id)
                    if istorage.exists(bag_name):
                        # delete the resource bag as the old bag is not valid
                        istorage.delete(bag_name)
                        print("Deleted bag for resource ID:" + str(res.short_id))

                    resource_modified(res, res.creator)

                    log.info('Tif file conversion to VRT successful for resource:ID:{} '
                             'Title:{}'.format(res.short_id, res.metadata.title.value))
                else:
                    log.error('Tif file conversion to VRT unsuccessful for resource:ID:{} '
                              'Title:{}'.format(res.short_id, res.metadata.title.value))

                if os.path.exists(vrt_file_path):
                    shutil.rmtree(os.path.dirname(vrt_file_path))

        except:
            pass


def undo_migrate_tif_file(apps, schema_editor):
    # delete vrt file from each of the raster resources
    for res in RasterResource.objects.all():
        try:
            for res_file in res.files.all():
                file_ext = os.path.splitext(res_file.resource_file.name)[1]
                if file_ext == '.vrt':
                    file_name = os.path.basename(res_file.resource_file.name)
                    hydroshare.delete_resource_file(res.short_id, file_name, res.creator)
        except:
            pass


class Migration(migrations.Migration):

    dependencies = [
        ('hs_geo_raster_resource', '0004_auto_20151116_2257'),
    ]

    operations = [
        migrations.RunPython(code=migrate_tif_file, reverse_code=undo_migrate_tif_file),
    ]
