"""Define celery tasks for hs_core app."""

from __future__ import absolute_import

import os
import sys
import traceback
import zipfile
import logging


from celery import shared_task
from django.conf import settings

from hs_core.hydroshare import utils
from hs_core.hydroshare.hs_bagit import create_bag_files
from django_irods.storage import IrodsStorage
from theme.models import UserQuota

from django_irods.icommands import SessionException

from hs_core.models import BaseResource

# Pass 'django' into getLogger instead of __name__
# for celery tasks (as this seems to be the
# only way to successfully log in code executed
# by celery, despite our catch-all handler).
logger = logging.getLogger('django')


@shared_task
def add_zip_file_contents_to_resource(pk, zip_file_path):
    """Add zip file to existing resource and remove tmp zip file."""
    zfile = None
    resource = None
    try:
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
            resource.file_unpack_message = "Imported {0} of about {1} file(s) ...".format(
                i, num_files)
            resource.save()

        # This might make the resource unsuitable for public consumption
        resource.update_public_and_discoverable()
        # TODO: this is a bit of a lie because a different user requested the bag overwrite
        utils.resource_modified(resource, resource.creator, overwrite_bag=False)

        # Call success callback
        resource.file_unpack_message = None
        resource.file_unpack_status = 'Done'
        resource.save()

    except BaseResource.DoesNotExist:
        msg = "Unable to add zip file contents to non-existent resource {pk}."
        msg = msg.format(pk=pk)
        logger.error(msg)
    except Exception:
        exc_info = "".join(traceback.format_exception(*sys.exc_info()))
        if resource:
            resource.file_unpack_status = 'Error'
            resource.file_unpack_message = exc_info
            resource.save()

        if zfile:
            zfile.close()

        logger.error(exc_info)
    finally:
        # Delete upload file
        os.unlink(zip_file_path)


@shared_task
def delete_zip(zip_path):
    istorage = IrodsStorage()
    if istorage.exists(zip_path):
        istorage.delete(zip_path)


@shared_task
def create_temp_zip(resource_id, input_path, output_path, sf_aggregation):
    from hs_core.hydroshare.utils import get_resource_by_shortkey
    if sf_aggregation:
        pass
    res = get_resource_by_shortkey(resource_id)
    full_input_path = '{root_path}/{path}'.format(root_path=res.root_path, path=input_path)

    try:
        IrodsStorage().zipup(full_input_path, output_path)
    except SessionException as ex:
        logger.error(ex.stderr)
        return False
    return True


@shared_task
def create_bag_by_irods(resource_id):
    """Create a resource bag on iRODS side by running the bagit rule and ibun zip.

    This function runs as a celery task, invoked asynchronously so that it does not
    block the main web thread when it creates bags for very large files which will take some time.
    :param
    resource_id: the resource uuid that is used to look for the resource to create the bag for.

    :return: True if bag creation operation succeeds;
             False if there is an exception raised or resource does not exist.
    """
    from hs_core.hydroshare.utils import get_resource_by_shortkey

    res = get_resource_by_shortkey(resource_id)
    istorage = res.get_irods_storage()

    metadata_dirty = istorage.getAVU(res.root_path, 'metadata_dirty')
    # if metadata has been changed, then regenerate metadata xml files
    if metadata_dirty is None or metadata_dirty.lower() == "true":
        try:
            create_bag_files(res)
        except Exception as ex:
            logger.error('Failed to create bag files. Error:{}'.format(ex.message))
            return False

    bag_full_name = 'bags/{res_id}.zip'.format(res_id=resource_id)
    if res.resource_federation_path:
        irods_bagit_input_path = os.path.join(res.resource_federation_path, resource_id)
        is_exist = istorage.exists(irods_bagit_input_path)
        # check to see if bagit readme.txt file exists or not
        bagit_readme_file = '{fed_path}/{res_id}/readme.txt'.format(
            fed_path=res.resource_federation_path,
            res_id=resource_id)
        is_bagit_readme_exist = istorage.exists(bagit_readme_file)
        bagit_input_path = "*BAGITDATA='{path}'".format(path=irods_bagit_input_path)
        bagit_input_resource = "*DESTRESC='{def_res}'".format(
            def_res=settings.HS_IRODS_LOCAL_ZONE_DEF_RES)
        bag_full_name = os.path.join(res.resource_federation_path, bag_full_name)
        bagit_files = [
            '{fed_path}/{res_id}/bagit.txt'.format(fed_path=res.resource_federation_path,
                                                   res_id=resource_id),
            '{fed_path}/{res_id}/manifest-md5.txt'.format(
                fed_path=res.resource_federation_path, res_id=resource_id),
            '{fed_path}/{res_id}/tagmanifest-md5.txt'.format(
                fed_path=res.resource_federation_path, res_id=resource_id),
            '{fed_path}/bags/{res_id}.zip'.format(fed_path=res.resource_federation_path,
                                                  res_id=resource_id)
        ]
    else:
        is_exist = istorage.exists(resource_id)
        # check to see if bagit readme.txt file exists or not
        bagit_readme_file = '{res_id}/readme.txt'.format(res_id=resource_id)
        is_bagit_readme_exist = istorage.exists(bagit_readme_file)
        irods_dest_prefix = "/" + settings.IRODS_ZONE + "/home/" + settings.IRODS_USERNAME
        irods_bagit_input_path = os.path.join(irods_dest_prefix, resource_id)
        bagit_input_path = "*BAGITDATA='{path}'".format(path=irods_bagit_input_path)
        bagit_input_resource = "*DESTRESC='{def_res}'".format(
            def_res=settings.IRODS_DEFAULT_RESOURCE)
        bagit_files = [
            '{res_id}/bagit.txt'.format(res_id=resource_id),
            '{res_id}/manifest-md5.txt'.format(res_id=resource_id),
            '{res_id}/tagmanifest-md5.txt'.format(res_id=resource_id),
            'bags/{res_id}.zip'.format(res_id=resource_id)
        ]

    # only proceed when the resource is not deleted potentially by another request
    # when being downloaded
    if is_exist:
        # if bagit readme.txt does not exist, add it.
        if not is_bagit_readme_exist:
            from_file_name = getattr(settings, 'HS_BAGIT_README_FILE_WITH_PATH',
                                     'docs/bagit/readme.txt')
            istorage.saveFile(from_file_name, bagit_readme_file, True)

        # call iRODS bagit rule here
        bagit_rule_file = getattr(settings, 'IRODS_BAGIT_RULE',
                                  'hydroshare/irods/ruleGenerateBagIt_HS.r')

        try:
            # call iRODS run and ibun command to create and zip the bag, ignore SessionException
            # for now as a workaround which could be raised from potential race conditions when
            # multiple ibun commands try to create the same zip file or the very same resource
            # gets deleted by another request when being downloaded
            istorage.runBagitRule(bagit_rule_file, bagit_input_path, bagit_input_resource)
            istorage.zipup(irods_bagit_input_path, bag_full_name)
            istorage.setAVU(irods_bagit_input_path, 'bag_modified', "false")
            return True
        except SessionException as ex:
            # if an exception occurs, delete incomplete files potentially being generated by
            # iRODS bagit rule and zipping operations
            for fname in bagit_files:
                if istorage.exists(fname):
                    istorage.delete(fname)
            logger.error(ex.stderr)
            return False
    else:
        logger.error('Resource does not exist.')
        return False


@shared_task
def update_quota_usage_task(username):
    """update quota usage. This function runs as a celery task, invoked asynchronously with 1
    minute delay to give enough time for iRODS real time quota update micro-services to update
    quota usage AVU for the user before this celery task to check this AVU to get the updated
    quota usage for the user. Note iRODS micro-service quota update only happens on HydroShare
    iRODS data zone and user zone independently, so the aggregation of usage in both zones need
    to be accounted for in this function to update Django DB as an aggregated usage for hydroshare
    internal zone.
    :param
    username: the name of the user that needs to update quota usage for.
    :return: True if quota usage update succeeds;
             False if there is an exception raised or quota cannot be updated. See log for details.
    """
    hs_internal_zone = "hydroshare"
    uq = UserQuota.objects.filter(user__username=username, zone=hs_internal_zone).first()
    if uq is None:
        # the quota row does not exist in Django
        logger.error('quota row does not exist in Django for hydroshare zone for '
                     'user ' + username)
        return False

    attname = username + '-usage'
    istorage = IrodsStorage()
    # get quota size for user in iRODS data zone by retrieving AVU set on irods bagit path
    # collection
    try:
        uqDataZoneSize = istorage.getAVU(settings.IRODS_BAGIT_PATH, attname)
        if uqDataZoneSize is None:
            # user may not have resources in data zone, so corresponding quota size AVU may not
            # exist for this user
            uqDataZoneSize = -1
        else:
            uqDataZoneSize = float(uqDataZoneSize)
    except SessionException:
        # user may not have resources in data zone, so corresponding quota size AVU may not exist
        # for this user
        uqDataZoneSize = -1

    # get quota size for the user in iRODS user zone
    try:
        uz_bagit_path = os.path.join('/', settings.HS_USER_IRODS_ZONE, 'home',
                                     settings.HS_LOCAL_PROXY_USER_IN_FED_ZONE,
                                     settings.IRODS_BAGIT_PATH)
        uqUserZoneSize = istorage.getAVU(uz_bagit_path, attname)
        if uqUserZoneSize is None:
            # user may not have resources in user zone, so corresponding quota size AVU may not
            # exist for this user
            uqUserZoneSize = -1
        else:
            uqUserZoneSize = float(uqUserZoneSize)
    except SessionException:
        # user may not have resources in user zone, so corresponding quota size AVU may not exist
        # for this user
        uqUserZoneSize = -1

    if uqDataZoneSize < 0 and uqUserZoneSize < 0:
        logger.error('no quota size AVU in data zone and user zone for the user ' + username)
        return False
    elif uqUserZoneSize < 0:
        used_val = uqDataZoneSize
    elif uqDataZoneSize < 0:
        used_val = uqUserZoneSize
    else:
        used_val = uqDataZoneSize + uqUserZoneSize

    uq.update_used_value(used_val)

    return True
