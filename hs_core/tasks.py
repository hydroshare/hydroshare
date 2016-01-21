from __future__ import absolute_import

import os
import zipfile
import logging

from celery import shared_task

from hs_core.hydroshare import utils


@shared_task
def add_zip_file_contents_to_resource(pk, zip_file_path):
    zfile = None
    try:
        logger = logging.getLogger('django')
        resource = utils.get_resource_by_shortkey(pk, or_404=False)
        zfile = zipfile.ZipFile(zip_file_path)
        zcontents = utils.ZipContents(zfile)
        files = zcontents.get_files()

        for f in files:
            logger.debug("Adding file {0} to resource {1}".format(f.name, pk))
            utils.add_file_to_resource(resource, f)

        # TODO: Call success callback
    except Exception as e:
        if zfile:
            zfile.close()
        # TODO: Call error callback
        raise e
    finally:
        # Delete upload file
        os.unlink(zip_file_path)
