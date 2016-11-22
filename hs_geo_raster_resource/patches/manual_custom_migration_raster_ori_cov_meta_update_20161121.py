# This script is to update original coverage metadata to add crs string and crs datum info
# to all raster resources (github issue #1520)
# how to run:
# docker exec -i hydroshare python manage.py shell \
# < "hs_geo_raster_resource/patches/manual_custom_migration_raster_ori_cov_meta_update_20161121.py"
# Note: use "-i" instead of "-it" in above command as
# the latter may cause error "cannot enable tty mode on non tty input"

from __future__ import unicode_literals

import os
import shutil
import logging
import tempfile

from hs_core.hydroshare.utils import resource_modified, get_file_from_irods
from hs_geo_raster_resource import raster_meta_extract
from hs_geo_raster_resource.models import RasterResource


log = logging.getLogger()
copy_res_fail = []
meta_update_fail = []
meta_update_success = []

# start migration for each raster resource that has raster files
for res in RasterResource.objects.all():

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

        vrt_file_path = [os.path.join(temp_dir, f)
                         for f in os.listdir(temp_dir) if '.vrt' == f[-4:]].pop()

    except Exception as e:
        if os.path.isdir(temp_dir):
            shutil.rmtree(temp_dir)
        if os.path.isfile(res_file_tmp_path):
            shutil.rmtree(os.path.dirname(res_file_tmp_path))
        log.exception(e.message)
        copy_res_fail.append('{}:{}'.format(res.short_id, res.metadata.title.value))
        continue

    # update the metadata for the original coverage information of all the raster resources
    try:
        if temp_dir and vrt_file_path:
            meta_updated = False

            # extract meta.
            # the reason to change current working directory to temp_dir is to make sure
            # the raster files can be found by Gdal for metadata extraction
            # when "relativeToVRT" parameter is set as "0"
            ori_dir = os.getcwd()
            os.chdir(temp_dir)
            res_md_dict = raster_meta_extract.get_raster_meta_dict(vrt_file_path)
            os.chdir(ori_dir)
            shutil.rmtree(temp_dir)

            # update original coverage information for datum and coordinate string in django
            if res.metadata.originalCoverage:
                res.metadata.originalCoverage.delete()
                v = {'value': res_md_dict['spatial_coverage_info']['original_coverage_info']}
                res.metadata.create_element('OriginalCoverage', **v)
                meta_updated = True

            # update the bag if meta is updated
            if meta_updated:
                resource_modified(res, res.creator)
                meta_update_success.append('{}:{}'.format(res.short_id,
                                                          res.metadata.title.value))

    except Exception as e:
        if os.path.isdir(temp_dir):
            shutil.rmtree(temp_dir)
        log.exception(e.message)
        meta_update_fail.append('{}:{}'.format(res.short_id, res.metadata.title.value))

# Print migration results
print 'Copy resource to temp folder failure: Number: {} List: {}'.\
    format(len(copy_res_fail), copy_res_fail)
print 'Meta update success: Number: {} List {}'.\
    format(len(meta_update_success), meta_update_success)
print 'Meta update fail: Number: {} List {}'.format(len(meta_update_fail), meta_update_fail)
