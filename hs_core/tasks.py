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
from hs_core.hydroshare.resource import get_activated_doi, get_resource_doi, \
    get_crossref_url, deposit_res_metadata_with_crossref


# Pass 'django' into getLogger instead of __name__
# for celery tasks (as this seems to be the
# only way to successfully log in code executed
# by celery, despite our catch-all handler).
logger = logging.getLogger('django')


@periodic_task(ignore_result=True, run_every=crontab(minute=0, hour=0))
def check_doi_activation():
    msg_lst = []
    # retrieve all published resources with failed metadata deposition with CrossRef if any and retry metadata deposition
    failed_resources = BaseResource.objects.filter(raccess__published=True, doi__contains='failure')
    for res in failed_resources:
        if res.metadata.dates.all().filter(type='published'):
            pub_date = res.metadata.dates.all().filter(type='published')[0]
            pub_date = pub_date.start_date.strftime('%m/%d/%Y')
            act_doi = get_activated_doi(res.doi)
            response = deposit_res_metadata_with_crossref(res)
            if response.status_code == status.HTTP_200_OK:
                # retry of metadata deposition succeeds, change resource flag from failure to pending
                res.doi = get_resource_doi(act_doi, 'pending')
                res.save()
            else:
                # retry of metadata deposition failed again, notify admin
                msg_lst.append("Metadata deposition with CrossRef for the published resource DOI {res_doi} "
                               "failed again after retry with first metadata deposition requested since {pub_date}.".format(res_doi=act_doi, pub_date=pub_date))
                logger.debug(response.content)
        else:
           msg_lst.append("{res_id} does not have published date in its metadata.".format(res_id=res.short_id))

    pending_resources = BaseResource.objects.filter(raccess__published=True, doi__contains='pending')
    for res in pending_resources:
        if res.metadata.dates.all().filter(type='published'):
            pub_date = res.metadata.dates.all().filter(type='published')[0]
            pub_date = pub_date.start_date.strftime('%m/%d/%Y')
            act_doi = get_activated_doi(res.doi)
            main_url = get_crossref_url()
            response = requests.get('{MAIN_URL}servlet/submissionDownload?usr={USERNAME}&pwd={PASSWORD}&doi_batch_id={DOI_BATCH_ID}&type={TYPE}'.format(
                                MAIN_URL=main_url, USERNAME=settings.CROSSREF_LOGIN_ID, PASSWORD=settings.CROSSREF_LOGIN_PWD, DOI_BATCH_ID=res.short_id, TYPE='result'))
            root = ElementTree.fromstring(response.content)
            rec_cnt_elem = root.find('.//record_count')
            success_cnt_elem = root.find('.//success_count')
            success = False
            if rec_cnt_elem is not None and success_cnt_elem is not None:
                rec_cnt = rec_cnt_elem.text
                success_cnt = success_cnt_elem.text
                if rec_cnt == success_cnt:
                    res.doi = act_doi
                    res.save()
                    success = True
            if not success:
                msg_lst.append("Published resource DOI {res_doi} is not yet activated with request data deposited since {pub_date}.".format(res_doi=act_doi, pub_date=pub_date))
                logger.debug(response.content)
        else:
           msg_lst.append("{res_id} does not have published date in its metadata.".format(res_id=res.short_id))

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
            resource.file_unpack_message = "Imported {0} of about {1} file(s) ...".format(i, num_files)
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