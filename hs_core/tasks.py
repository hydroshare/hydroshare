from __future__ import absolute_import

import os
import sys
import traceback
import zipfile
import logging
import time

from celery import shared_task

from hs_core.hydroshare import utils
from hs_core.models import BaseResource


@shared_task
def add_zip_file_contents_to_resource(pk, zip_file_path):
    zfile = None
    try:
        logger = logging.getLogger('django')
        resource = utils.get_resource_by_shortkey(pk, or_404=False)
        zfile = zipfile.ZipFile(zip_file_path)
        num_files = len(zfile.infolist())
        zcontents = utils.ZipContents(zfile)
        files = zcontents.get_files()

        resource.file_unpack_status = 'Running'
        resource.save()

        for i, f in enumerate(files):
            logger.debug("Adding file {0} to resource {1}".format(f.name, pk))
            utils.add_file_to_resource(resource, f)
            resource.file_unpack_message = "Imported {0} of about {1} file(s) ...".format(i, num_files)
            resource.save()

        # Call success callback
        resource.file_unpack_message = None
        resource.file_unpack_status = 'Done'
        resource.save()

    except BaseResource.DoesNotExist:
        raise
    except Exception as e:

        resource.file_unpack_status = 'Error'
        exc_info = "".join(traceback.format_exception(*sys.exc_info()))
        resource.file_unpack_message = exc_info[:1024]
        resource.save()

        if zfile:
            zfile.close()

        raise e
    finally:
        # Delete upload file
        os.unlink(zip_file_path)
