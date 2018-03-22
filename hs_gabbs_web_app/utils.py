from __future__ import absolute_import

import os
import logging

from django.conf import settings

from hs_core.hydroshare.utils import get_resource_by_shortkey


logger = logging.getLogger(__name__)


def push_res_to_geohub(url, user, shortkey):
    # push resource (with uuid as shortkey input) to geohub iRODS zone for geohub tool launch and
    # return the new tool launch url. If no valid file is included in the resource, an empty url
    # will be returned so that the calling routine will not redirect to mygeohub for tool launch
    res = get_resource_by_shortkey(shortkey)
    istorage = res.get_irods_storage()
    src_path = res.root_path
    # delete all temporary resources copied to this user's space before pushing this resource
    dest_path = os.path.join(settings.GEOHUB_HS_IRODS_PATH, user.username)
    if istorage.exists(dest_path):
        istorage.delete(dest_path)
    dest_path = os.path.join(dest_path, shortkey)
    istorage.copyFiles(src_path, dest_path, settings.GEOHUB_HS_IRODS_RESC)
    try:
        fname = res.get_res_file_name()
    except Exception as ex:
        logger.debug("Exception raised when calling get_res_file_name on resource {0}: {1}".format(
            shortkey, ex.message))
        fname = ''
    if fname:
        if not url.endswith('/'):
            url += '/'
        url += fname
    else:
        # if valid file is not included in the resource, clear the url so the calling routine
        # will not redirect to mygeohub for tool launch
        url = ''
    return url
