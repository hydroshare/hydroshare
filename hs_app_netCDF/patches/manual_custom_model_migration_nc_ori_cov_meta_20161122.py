"""
This script is to change the resource status as modified to update the resource science metadata
xml file for original coverage metadata (github issue #1586)

This should be run after model migration of 0005_auto_20161111_2322.py

how to run:
$ docker exec -i hydroshare python manage.py shell \
< "hs_app_netCDF/patchesual_custom_model_migration_nc_ori_cov_meta_20161122.py"

Note: use "-i" instead of "-it" in above command as
the latter may cause error "cannot enable tty mode on non tty input"
"""

from __future__ import unicode_literals

import os
import tempfile
import shutil

from hs_core.hydroshare.utils import resource_modified, get_file_from_irods
from hs_app_netCDF.models import NetcdfResource
from hs_app_netCDF.nc_functions.nc_meta import get_nc_meta_dict

copy_res_fail = []
meta_update_fail = []
meta_update_success = []

for res in NetcdfResource.objects.all():
    # copy all the resource files to temp dir
    temp_dir = ''
    res_file_tmp_path = ''
    try:
        temp_dir = tempfile.mkdtemp()
        for res_file in res.files.all():
            res_file_tmp_path = get_file_from_irods(res_file)
            shutil.copy(res_file_tmp_path,
                        os.path.join(temp_dir, os.path.basename(res_file_tmp_path)))
            shutil.rmtree(os.path.dirname(res_file_tmp_path))

        nc_file_path = [os.path.join(temp_dir, f)
                        for f in os.listdir(temp_dir) if '.nc' == f[-3:]].pop()
    except Exception as e:
        if os.path.isdir(temp_dir):
            shutil.rmtree(temp_dir)
        if os.path.isfile(res_file_tmp_path):
            shutil.rmtree(os.path.dirname(res_file_tmp_path))
        copy_res_fail.append('{}:{}'.format(res.short_id, res.metadata.title.value))
        continue

    # update the metadata for the original coverage information of all the raster resources
    try:
        if temp_dir and nc_file_path:
            meta_updated = False

            # extract meta dict
            res_dublin_core_meta = get_nc_meta_dict(nc_file_path).get('dublin_core_meta', {})
            shutil.rmtree(temp_dir)

            # update the ori metadata
            if res_dublin_core_meta.get('original-box'):
                res.metadata.ori_coverage.all().delete()
                if res_dublin_core_meta.get('projection-info'):
                    res.metadata.create_element(
                        'originalcoverage',
                        value=res_dublin_core_meta['original-box'],
                        projection_string_type=res_dublin_core_meta['projection-info']['type'],
                        projection_string_text=res_dublin_core_meta['projection-info']['text'],
                        datum=res_dublin_core_meta['projection-info']['datum'])
                else:
                    res.metadata.create_element('originalcoverage',
                                                value=res_dublin_core_meta['original-box'])
                meta_updated = True

            # update the bag if meta is updated
            if meta_updated:
                resource_modified(res, res.creator)
                meta_update_success.append('{}:{}'.format(res.short_id,
                                                          res.metadata.title.value))

    except Exception as e:
        if os.path.isdir(temp_dir):
            shutil.rmtree(temp_dir)
        meta_update_fail.append('{}:{}'.format(res.short_id, res.metadata.title.value))
        print e.message

print 'Meta update success:Number: {} List {}'.format(len(meta_update_success), meta_update_success)
print 'Meta update fail:Number: {} List {}'.format(len(meta_update_fail), meta_update_fail)
