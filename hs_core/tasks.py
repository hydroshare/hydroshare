from __future__ import absolute_import

import os
import sys
import traceback
import zipfile
import logging

import requests

from xml.etree import ElementTree

from rest_framework import status

from django.conf import settings
from django.core.mail import send_mail

from celery.task import periodic_task
from celery.schedules import crontab
from celery import shared_task

from hs_core.models import BaseResource
from hs_core.hydroshare import utils
from hs_core.hydroshare.hs_bagit import create_bag_files
from hs_core.hydroshare.resource import get_activated_doi, get_resource_doi, \
    get_crossref_url, deposit_res_metadata_with_crossref

from django_irods.icommands import SessionException


# Pass 'django' into getLogger instead of __name__
# for celery tasks (as this seems to be the
# only way to successfully log in code executed
# by celery, despite our catch-all handler).
logger = logging.getLogger('django')


@periodic_task(ignore_result=True, run_every=crontab(minute=0, hour=0))
def check_doi_activation():
    msg_lst = []
    # retrieve all published resources with failed metadata deposition with CrossRef if any and
    # retry metadata deposition
    failed_resources = BaseResource.objects.filter(raccess__published=True, doi__contains='failure')
    for res in failed_resources:
        if res.metadata.dates.all().filter(type='published'):
            pub_date = res.metadata.dates.all().filter(type='published')[0]
            pub_date = pub_date.start_date.strftime('%m/%d/%Y')
            act_doi = get_activated_doi(res.doi)
            response = deposit_res_metadata_with_crossref(res)
            if response.status_code == status.HTTP_200_OK:
                # retry of metadata deposition succeeds, change resource flag from failure
                # to pending
                res.doi = get_resource_doi(act_doi, 'pending')
                res.save()
            else:
                # retry of metadata deposition failed again, notify admin
                msg_lst.append("Metadata deposition with CrossRef for the published resource "
                               "DOI {res_doi} failed again after retry with first metadata "
                               "deposition requested since {pub_date}.".format(res_doi=act_doi,
                                                                               pub_date=pub_date))
                logger.debug(response.content)
        else:
            msg_lst.append("{res_id} does not have published date in its metadata.".format(
                res_id=res.short_id))

    pending_resources = BaseResource.objects.filter(raccess__published=True,
                                                    doi__contains='pending')
    for res in pending_resources:
        if res.metadata.dates.all().filter(type='published'):
            pub_date = res.metadata.dates.all().filter(type='published')[0]
            pub_date = pub_date.start_date.strftime('%m/%d/%Y')
            act_doi = get_activated_doi(res.doi)
            main_url = get_crossref_url()
            req_str = '{MAIN_URL}servlet/submissionDownload?usr={USERNAME}&pwd=' \
                      '{PASSWORD}&doi_batch_id={DOI_BATCH_ID}&type={TYPE}'
            response = requests.get(req_str.format(MAIN_URL=main_url,
                                                   USERNAME=settings.CROSSREF_LOGIN_ID,
                                                   PASSWORD=settings.CROSSREF_LOGIN_PWD,
                                                   DOI_BATCH_ID=res.short_id,
                                                   TYPE='result'))
            root = ElementTree.fromstring(response.content)
            rec_cnt_elem = root.find('.//record_count')
            failure_cnt_elem = root.find('.//failure_count')
            success = False
            if rec_cnt_elem is not None and failure_cnt_elem is not None:
                rec_cnt = int(rec_cnt_elem.text)
                failure_cnt = int(failure_cnt_elem.text)
                if rec_cnt > 0 and failure_cnt == 0:
                    res.doi = act_doi
                    res.save()
                    success = True
            if not success:
                msg_lst.append("Published resource DOI {res_doi} is not yet activated with request "
                               "data deposited since {pub_date}.".format(res_doi=act_doi,
                                                                         pub_date=pub_date))
                logger.debug(response.content)
        else:
            msg_lst.append("{res_id} does not have published date in its metadata.".format(
                res_id=res.short_id))

    if msg_lst:
        email_msg = '\n'.join(msg_lst)
        subject = 'Notification of pending DOI deposition/activation of published resources'
        # send email for people monitoring and follow-up as needed
        send_mail(subject, email_msg, settings.DEFAULT_FROM_EMAIL, [settings.DEFAULT_SUPPORT_EMAIL])


@shared_task
def add_zip_file_contents_to_resource(pk, zip_file_path):
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

        # Call success callback
        resource.file_unpack_message = None
        resource.file_unpack_status = 'Done'
        resource.save()

    except BaseResource.DoesNotExist:
        msg = "Unable to add zip file contents to non-existent resource {pk}."
        msg = msg.format(pk=pk)
        logger.error(msg)
    except:
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
def create_bag_by_irods(resource_id):
    """
    create a resource bag on iRODS side by running the bagit rule followed by ibun zipping
    operation. This function runs as a celery task, invoked asynchronously so that it does not
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
    if metadata_dirty.lower() == "true":
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
def check_irods_files():
    """
    Check every resource for iRODS file problems.

    This logs DEBUG messages for every problem it finds
    """
    for r in BaseResource.objects.all():
        r.check_irods_files()
