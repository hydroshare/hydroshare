"""Define celery tasks for hs_core app."""

from __future__ import absolute_import

import os
import sys
import traceback
import zipfile
import logging
import json

from datetime import datetime, timedelta, date
from xml.etree import ElementTree

import requests
from celery import shared_task
from celery.schedules import crontab
from celery.task import periodic_task
from django.conf import settings
from django.core.mail import send_mail
from rest_framework import status

from hs_core.hydroshare import utils
from hs_core.hydroshare.hs_bagit import create_bag_files
from hs_core.hydroshare.resource import get_activated_doi, get_resource_doi, \
    get_crossref_url, deposit_res_metadata_with_crossref
from django_irods.storage import IrodsStorage
from theme.models import UserQuota, QuotaMessage, UserProfile, User

from django_irods.icommands import SessionException

from hs_core.models import BaseResource
from theme.utils import get_quota_message

# Pass 'django' into getLogger instead of __name__
# for celery tasks (as this seems to be the
# only way to successfully log in code executed
# by celery, despite our catch-all handler).
logger = logging.getLogger('django')


# Currently there are two different cleanups scheduled.
# One is 20 minutes after creation, the other is nightly.
# TODO Clean up zipfiles in remote federated storage as well.
@periodic_task(ignore_result=True, run_every=crontab(minute=30, hour=23))
def nightly_zips_cleanup():
    # delete 2 days ago
    date_folder = (date.today() - timedelta(2)).strftime('%Y-%m-%d')
    zips_daily_date = "zips/{daily_date}".format(daily_date=date_folder)
    if __debug__:
        logger.debug("cleaning up {}".format(zips_daily_date))
    istorage = IrodsStorage()
    if istorage.exists(zips_daily_date):
        istorage.delete(zips_daily_date)
    federated_prefixes = BaseResource.objects.all().values_list('resource_federation_path')\
        .distinct()

    for p in federated_prefixes:
        prefix = p[0]  # strip tuple
        if prefix != "":
            zips_daily_date = "{prefix}/zips/{daily_date}"\
                .format(prefix=prefix, daily_date=date_folder)
            if __debug__:
                logger.debug("cleaning up {}".format(zips_daily_date))
            istorage = IrodsStorage("federated")
            if istorage.exists(zips_daily_date):
                istorage.delete(zips_daily_date)


@periodic_task(ignore_result=True, run_every=crontab(minute=0, hour=0))
def sync_email_subscriptions():
    sixty_days = datetime.today() - timedelta(days=60)
    active_subscribed = UserProfile.objects.filter(email_opt_out=False,
                                                   user__last_login__gte=sixty_days,
                                                   user__is_active=True)
    sync_mailchimp(active_subscribed, settings.MAILCHIMP_ACTIVE_SUBSCRIBERS)
    subscribed = UserProfile.objects.filter(email_opt_out=False, user__is_active=True)
    sync_mailchimp(subscribed, settings.MAILCHIMP_SUBSCRIBERS)


def sync_mailchimp(active_subscribed, list_id):
    session = requests.Session()
    url = "https://us3.api.mailchimp.com/3.0/lists/{list_id}/members"
    # get total members
    response = session.get(url.format(list_id=list_id), auth=requests.auth.HTTPBasicAuth(
        'hs-celery', settings.MAILCHIMP_PASSWORD))
    total_items = json.loads(response.content)["total_items"]
    # get list of all member ids
    response = session.get((url + "?offset=0&count={total_items}").format(list_id=list_id,
                                                                          total_items=total_items),
                           auth=requests.auth.HTTPBasicAuth('hs-celery',
                                                            settings.MAILCHIMP_PASSWORD))
    # clear the email list
    delete_count = 0
    for member in json.loads(response.content)["members"]:
        if member["status"] == "subscribed":
            session_response = session.delete(
                (url + "/{id}").format(list_id=list_id, id=member["id"]),
                auth=requests.auth.HTTPBasicAuth('hs-celery', settings.MAILCHIMP_PASSWORD))
            if session_response.status_code != 204:
                logger.info("Expected 204 status code, got " + str(session_response.status_code))
                logger.debug(session_response.content)
            else:
                delete_count += 1
    # add active subscribed users to mailchimp
    add_count = 0
    for subscriber in active_subscribed:
        json_data = {"email_address": subscriber.user.email, "status": "subscribed",
                     "merge_fields": {"FNAME": subscriber.user.first_name,
                                      "LNAME": subscriber.user.last_name}}
        session_response = session.post(
            url.format(list_id=list_id), json=json_data, auth=requests.auth.HTTPBasicAuth(
                'hs-celery', settings.MAILCHIMP_PASSWORD))
        if session_response.status_code != 200:
            logger.info("Expected 200 status code, got " + str(session_response.status_code))
            logger.debug(session_response.content)
        else:
            add_count += 1
    if delete_count == active_subscribed.count():
        logger.info("successfully cleared mailchimp for list id " + list_id)
    else:
        logger.info(
            "cleared " + str(delete_count) + " out of " + str(
                active_subscribed.count()) + " for list id " + list_id)

    if active_subscribed.count() == add_count:
        logger.info("successfully synced all subscriptions for list id " + list_id)
    else:
        logger.info("added " + str(add_count) + " out of " + str(
            active_subscribed.count()) + " for list id " + list_id)


@periodic_task(ignore_result=True, run_every=crontab(minute=0, hour=0))
def manage_task_nightly():
    # The nightly running task do DOI activation check

    # Check DOI activation on failed and pending resources and send email.
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


@periodic_task(ignore_result=True, run_every=crontab(minute=15, hour=0, day_of_week=1,
                                                     day_of_month='1-7'))
def send_over_quota_emails():
    # check over quota cases and send quota warning emails as needed
    hs_internal_zone = "hydroshare"
    if not QuotaMessage.objects.exists():
        QuotaMessage.objects.create()
    qmsg = QuotaMessage.objects.first()
    users = User.objects.filter(is_active=True).filter(is_superuser=False).all()
    for u in users:
        uq = UserQuota.objects.filter(user__username=u.username, zone=hs_internal_zone).first()
        if uq:
            used_percent = uq.used_percent
            if used_percent >= qmsg.soft_limit_percent:
                if used_percent >= 100 and used_percent < qmsg.hard_limit_percent:
                    if uq.remaining_grace_period < 0:
                        # triggers grace period counting
                        uq.remaining_grace_period = qmsg.grace_period
                    elif uq.remaining_grace_period > 0:
                        # reduce remaining_grace_period by one day
                        uq.remaining_grace_period -= 1
                elif used_percent >= qmsg.hard_limit_percent:
                    # set grace period to 0 when user quota exceeds hard limit
                    uq.remaining_grace_period = 0
                uq.save()

                if u.first_name and u.last_name:
                    sal_name = '{} {}'.format(u.first_name, u.last_name)
                elif u.first_name:
                    sal_name = u.first_name
                elif u.last_name:
                    sal_name = u.last_name
                else:
                    sal_name = u.username

                msg_str = 'Dear ' + sal_name + ':\n\n'

                ori_qm = get_quota_message(u)
                # make embedded settings.DEFAULT_SUPPORT_EMAIL clickable with subject auto-filled
                replace_substr = "<a href='mailto:{0}?subject=Request more quota'>{0}</a>".format(
                    settings.DEFAULT_SUPPORT_EMAIL)
                new_qm = ori_qm.replace(settings.DEFAULT_SUPPORT_EMAIL, replace_substr)
                msg_str += new_qm

                msg_str += '\n\nHydroShare Support'
                subject = 'Quota warning'
                try:
                    # send email for people monitoring and follow-up as needed
                    send_mail(subject, '', settings.DEFAULT_FROM_EMAIL,
                              [u.email, settings.DEFAULT_SUPPORT_EMAIL],
                              html_message=msg_str)
                except Exception as ex:
                    logger.debug("Failed to send quota warning email: " + ex.message)
            else:
                if uq.remaining_grace_period >= 0:
                    # turn grace period off now that the user is below quota soft limit
                    uq.remaining_grace_period = -1
                    uq.save()
        else:
            logger.debug('user ' + u.username + ' does not have UserQuota foreign key relation')


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
def delete_zip(zip_path):
    istorage = IrodsStorage()
    if istorage.exists(zip_path):
        istorage.delete(zip_path)


@shared_task
def create_temp_zip(resource_id, input_path, output_path, sf_aggregation, sf_zip=False):
    """ Create temporary zip file from input_path and store in output_path
    :param input_path: full irods path of input starting with federation path
    :param output_path: full irods path of output starting with federation path
    :param sf_aggregation: if True, include logical metadata files
    """
    from hs_core.hydroshare.utils import get_resource_by_shortkey
    res = get_resource_by_shortkey(resource_id)
    istorage = res.get_irods_storage()  # invoke federated storage as necessary

    if res.resource_type == "CompositeResource":
        if '/data/contents/' in input_path:
            short_path = input_path.split('/data/contents/')[1]  # strip /data/contents/
            res.create_aggregation_xml_documents(aggregation_name=short_path)
        else:  # all metadata included, e.g., /data/*
            res.create_aggregation_xml_documents()

    try:
        if sf_zip:
            # input path points to single file aggregation
            # ensure that foo.zip contains aggregation metadata
            # by copying these into a temp subdirectory foo/foo parallel to where foo.zip is stored
            temp_folder_name, ext = os.path.splitext(output_path)  # strip zip to get scratch dir
            head, tail = os.path.split(temp_folder_name)  # tail is unqualified folder name "foo"
            out_with_folder = os.path.join(temp_folder_name, tail)  # foo/foo is subdir to zip
            istorage.copyFiles(input_path, out_with_folder)
            if sf_aggregation:
                try:
                    istorage.copyFiles(input_path + '_resmap.xml',  out_with_folder + '_resmap.xml')
                except SessionException:
                    logger.error("cannot copy {}".format(input_path + '_resmap.xml'))
                try:
                    istorage.copyFiles(input_path + '_meta.xml', out_with_folder + '_meta.xml')
                except SessionException:
                    logger.error("cannot copy {}".format(input_path + '_meta.xml'))
            istorage.zipup(temp_folder_name, output_path)
            istorage.delete(temp_folder_name)  # delete working directory; this isn't the zipfile
        else:  # regular folder to zip
            istorage.zipup(input_path, output_path)
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
            def_res=settings.HS_IRODS_USER_ZONE_DEF_RES)
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
                                     settings.HS_IRODS_PROXY_USER_IN_USER_ZONE,
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


@shared_task
def update_web_services(services_url, api_token, timeout, publish_urls, res_id):
    """Update web services hosted by GeoServer and HydroServer.

    This function sends a resource id to the HydroShare web services manager
    application, which will check the current status of the resource and register
    or unregister services hosted by GeoServer and HydroServer.
    The HydroShare web services manager will return a list of endpoint URLs
    for both the resource and individual aggregations. If publish_urls is set to
    True, these endpoints will be added to the extra metadata fields of the
    resource and aggregations.
    """
    session = requests.Session()
    session.headers.update(
        {"Authorization": " ".join(("Token", str(api_token)))}
    )

    rest_url = str(services_url) + "/" + str(res_id) + "/"

    try:
        response = session.post(rest_url, timeout=timeout)

        if publish_urls and response.status_code == status.HTTP_201_CREATED:
            try:

                resource = utils.get_resource_by_shortkey(res_id)
                response_content = json.loads(response.content)

                for key, value in response_content["resource"].iteritems():
                    resource.extra_metadata[key] = value
                    resource.save()

                for url in response_content["content"]:
                    lf = resource.logical_files[[i.aggregation_name for i in
                                                resource.logical_files].index(
                                                    url["layer_name"].encode("utf-8")
                                                )]
                    lf.metadata.extra_metadata["Web Services URL"] = url["message"]
                    lf.metadata.save()

            except Exception as e:
                logger.error(e)
                return e

        return response

    except (requests.exceptions.RequestException, ValueError) as e:
        logger.error(e)
        return e
