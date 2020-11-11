"""Define celery tasks for hs_core app."""

import os
import sys
import traceback
import zipfile
import logging
import json

from celery.signals import task_postrun
from datetime import datetime, timedelta, date
from xml.etree import ElementTree

import requests
from celery import shared_task
from celery.schedules import crontab
from celery.task import periodic_task
from django.conf import settings
from django.core.mail import send_mail
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import transaction
from rest_framework import status

from hs_access_control.models import GroupMembershipRequest
from hs_core.hydroshare import utils, create_empty_resource
from hs_core.hydroshare.hs_bagit import create_bag_files, create_bag
from hs_core.hydroshare.resource import get_activated_doi, get_resource_doi, \
    get_crossref_url, deposit_res_metadata_with_crossref
from hs_core.task_utils import get_or_create_task_notification
from hs_core.signals import post_delete_resource
from hs_odm2.models import ODM2Variable
from django_irods.storage import IrodsStorage
from theme.models import UserQuota, QuotaMessage, UserProfile, User
from hs_collection_resource.models import CollectionDeletedResource
from django_irods.icommands import SessionException
from celery.result import states

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
    total_items = json.loads(response.content.decode())["total_items"]
    # get list of all member ids
    response = session.get((url + "?offset=0&count={total_items}").format(list_id=list_id,
                                                                          total_items=total_items),
                           auth=requests.auth.HTTPBasicAuth('hs-celery',
                                                            settings.MAILCHIMP_PASSWORD))
    # clear the email list
    delete_count = 0
    for member in json.loads(response.content.decode())["members"]:
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
                # create bag and compute checksum for published resource to meet DataONE requirement
                create_bag_by_irods(res.short_id)
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
                    # create bag and compute checksum for published resource to meet DataONE requirement
                    create_bag_by_irods(res.short_id)
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
                if settings.DEBUG:
                    logger.info("quota warning email not sent out on debug server but logged instead: "
                                "{}".format(msg_str))
                else:
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
def create_temp_zip(resource_id, input_path, output_path, aggregation_name=None, sf_zip=False, download_path='',
                    request_username=None):
    """ Create temporary zip file from input_path and store in output_path
    :param resource_id: the short_id of a resource
    :param input_path: full irods path of input starting with federation path
    :param output_path: full irods path of output starting with federation path
    :param aggregation_name: The name of the aggregation to zip
    :param sf_zip: signals a single file to zip
    :param download_path: download path to return as task payload
    :param request_username: the username of the requesting user
    """
    from hs_core.hydroshare.utils import get_resource_by_shortkey
    res = get_resource_by_shortkey(resource_id)
    aggregation = None
    if aggregation_name:
        aggregation = res.get_aggregation_by_aggregation_name(aggregation_name)
    istorage = res.get_irods_storage()  # invoke federated storage as necessary

    if res.resource_type == "CompositeResource":
        if '/data/contents/' in input_path:
            short_path = input_path.split('/data/contents/')[1]  # strip /data/contents/
            res.create_aggregation_xml_documents(path=short_path)
        else:  # all metadata included, e.g., /data/*
            res.create_aggregation_xml_documents()

    if aggregation or sf_zip:
        # input path points to single file aggregation
        # ensure that foo.zip contains aggregation metadata
        # by copying these into a temp subdirectory foo/foo parallel to where foo.zip is stored
        temp_folder_name, ext = os.path.splitext(output_path)  # strip zip to get scratch dir
        head, tail = os.path.split(temp_folder_name)  # tail is unqualified folder name "foo"
        out_with_folder = os.path.join(temp_folder_name, tail)  # foo/foo is subdir to zip
        istorage.copyFiles(input_path, out_with_folder)
        if aggregation:
            try:
                istorage.copyFiles(aggregation.map_file_path,  temp_folder_name)
            except SessionException:
                logger.error("cannot copy {}".format(aggregation.map_file_path))
            try:
                istorage.copyFiles(aggregation.metadata_file_path, temp_folder_name)
            except SessionException:
                logger.error("cannot copy {}".format(aggregation.metadata_file_path))
            for file in aggregation.files.all():
                try:
                    istorage.copyFiles(file.storage_path, temp_folder_name)
                except SessionException:
                    logger.error("cannot copy {}".format(file.storage_path))
        istorage.zipup(temp_folder_name, output_path)
        istorage.delete(temp_folder_name)  # delete working directory; this isn't the zipfile
    else:  # regular folder to zip
        istorage.zipup(input_path, output_path)
    return download_path


@shared_task
def create_bag_by_irods(resource_id, request_username=None):
    """Create a resource bag on iRODS side by running the bagit rule and ibun zip.
    This function runs as a celery task, invoked asynchronously so that it does not
    block the main web thread when it creates bags for very large files which will take some time.
    :param
    resource_id: the resource uuid that is used to look for the resource to create the bag for.
    :return: bag_url if bag creation operation succeeds or
             raise an exception if resource does not exist or any other issues that prevent bags from being created.
    """
    res = utils.get_resource_by_shortkey(resource_id)

    istorage = res.get_irods_storage()

    bag_path = res.bag_path

    metadata_dirty = istorage.getAVU(res.root_path, 'metadata_dirty')
    # if metadata has been changed, then regenerate metadata xml files
    if metadata_dirty is None or metadata_dirty.lower() == "true":
        create_bag_files(res)

    irods_bagit_input_path = res.get_irods_path(resource_id, prepend_short_id=False)
    # check to see if bagit readme.txt file exists or not
    bagit_readme_file = res.get_irods_path('readme.txt')
    is_bagit_readme_exist = istorage.exists(bagit_readme_file)
    if irods_bagit_input_path.startswith(resource_id):
        # resource is in data zone, need to append the full path for iRODS bagit rule execution
        irods_dest_prefix = "/" + settings.IRODS_ZONE + "/home/" + settings.IRODS_USERNAME
        irods_bagit_input_path = os.path.join(irods_dest_prefix, resource_id)
        bagit_input_resource = "*DESTRESC='{def_res}'".format(
            def_res=settings.IRODS_DEFAULT_RESOURCE)
    else:
        # this will need to be changed with the default resource in whatever federated zone the
        # resource is stored in when we have such use cases to support
        bagit_input_resource = "*DESTRESC='{def_res}'".format(
            def_res=settings.HS_IRODS_USER_ZONE_DEF_RES)

    bagit_input_path = "*BAGITDATA='{path}'".format(path=irods_bagit_input_path)

    bagit_files = [
        res.get_irods_path('bagit.txt'),
        res.get_irods_path('manifest-md5.txt'),
        res.get_irods_path('tagmanifest-md5.txt'),
        bag_path
    ]

    # only proceed when the resource is not deleted potentially by another request
    # when being downloaded
    is_exist = istorage.exists(irods_bagit_input_path)
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
            istorage.zipup(irods_bagit_input_path, bag_path)
            if res.raccess.published:
                # compute checksum to meet DataONE distribution requirement
                chksum = istorage.checksum(bag_path)
                res.bag_checksum = chksum
            istorage.setAVU(irods_bagit_input_path, 'bag_modified', "false")
            return res.bag_url
        except SessionException as ex:
            # if an exception occurs, delete incomplete files potentially being generated by
            # iRODS bagit rule and zipping operations
            for fname in bagit_files:
                if istorage.exists(fname):
                    istorage.delete(fname)
            raise SessionException(-1, '', ex.stderr)
    else:
        raise ObjectDoesNotExist('Resource {} does not exist.'.format(resource_id))


@shared_task
def delete_resource_task(resource_id, request_username=None):
    """Delete a resource
    :param
    resource_id: the resource uuid that is used to look for the resource to delete.
    :return: resource_id if delete operation succeeds
             raise an exception if there were errors.
    """
    res = utils.get_resource_by_shortkey(resource_id)
    res_title = res.metadata.title
    res_type = res.resource_type
    resource_related_collections = [col for col in res.collections.all()]
    owners_list = [owner for owner in res.raccess.owners.all()]
    if res.metadata.relations.all().filter(type='isReplacedBy').exists():
        raise ValidationError('An obsoleted resource in the middle of the obsolescence chain '
                              'cannot be deleted.')

    with transaction.atomic():
        # when the most recent version of a resource in an obsolescence chain is deleted, the previous
        # version in the chain needs to be set as the "active" version by deleting "isReplacedBy"
        # relation element
        if res.metadata.relations.all().filter(type='isVersionOf').exists():
            is_version_of_res_link = \
                res.metadata.relations.all().filter(type='isVersionOf').first().value
            idx = is_version_of_res_link.rindex('/')
            if idx == -1:
                obsolete_res_id = is_version_of_res_link
            else:
                obsolete_res_id = is_version_of_res_link[idx + 1:]
            obsolete_res = utils.get_resource_by_shortkey(obsolete_res_id)
            if obsolete_res.metadata.relations.all().filter(type='isReplacedBy').exists():
                eid = obsolete_res.metadata.relations.all().filter(type='isReplacedBy').first().id
                obsolete_res.metadata.delete_element('relation', eid)
                # also make this obsoleted resource editable if not published now that it becomes the latest version
                if not obsolete_res.raccess.published:
                    obsolete_res.raccess.immutable = False
                    obsolete_res.raccess.save()

        res.delete()
        if request_username:
            # if the deleted resource is part of any collection resource, then for each of those collection
            # create a CollectionDeletedResource object which can then be used to list collection deleted
            # resources on collection resource landing page
            for collection_res in resource_related_collections:
                o = CollectionDeletedResource.objects.create(
                    resource_title=res_title,
                    deleted_by=User.objects.get(username=request_username),
                    resource_id=resource_id,
                    resource_type=res_type,
                    collection=collection_res
                )
                o.resource_owners.add(*owners_list)

        post_delete_resource.send(sender=type(res), username=request_username,
                                  resource_id=resource_id, resource_title=res_title)

        # return the page URL to redirect to after resource deletion task is complete
        return '/my-resources/'


@shared_task
def copy_resource_task(ori_res_id, new_res_id=None, request_username=None):
    try:
        new_res = None
        if not new_res_id:
            new_res = create_empty_resource(ori_res_id, request_username, action='copy')
            new_res_id = new_res.short_id
        utils.copy_resource_files_and_AVUs(ori_res_id, new_res_id)
        ori_res = utils.get_resource_by_shortkey(ori_res_id)
        if not new_res:
            new_res = utils.get_resource_by_shortkey(new_res_id)
        utils.copy_and_create_metadata(ori_res, new_res)

        hs_identifier = ori_res.metadata.identifiers.all().filter(name="hydroShareIdentifier")[0]
        if hs_identifier:
            new_res.metadata.create_element('source', derived_from=hs_identifier.url)

        if ori_res.resource_type.lower() == "collectionresource":
            # clone contained_res list of original collection and add to new collection
            # note that new collection will not contain "deleted resources"
            new_res.resources = ori_res.resources.all()

        # create bag for the new resource
        create_bag(new_res)
        return new_res.get_absolute_url()
    except Exception as ex:
        if new_res:
            new_res.delete()
        raise utils.ResourceCopyException(str(ex))


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
                response_content = json.loads(response.content.decode())

                for key, value in response_content["resource"].items():
                    resource.extra_metadata[key] = value
                    resource.save()

                for url in response_content["content"]:
                    logical_files = list(resource.logical_files)
                    lf = logical_files[[i.aggregation_name for i in
                                        logical_files].index(
                                                    url["layer_name"].encode()
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


@shared_task
def resource_debug(resource_id):
    """Update web services hosted by GeoServer and HydroServer.
    """
    from hs_core.hydroshare.utils import get_resource_by_shortkey

    resource = get_resource_by_shortkey(resource_id)
    from hs_core.management.utils import check_irods_files
    return check_irods_files(resource, log_errors=False, return_errors=True)


@shared_task
def unzip_task(user_pk, res_id, zip_with_rel_path, bool_remove_original, overwrite=False, auto_aggregate=False,
               ingest_metadata=False):
    from hs_core.views.utils import unzip_file
    user = User.objects.get(pk=user_pk)
    unzip_file(user, res_id, zip_with_rel_path, bool_remove_original, overwrite, auto_aggregate, ingest_metadata)


@periodic_task(ignore_result=True, run_every=crontab(minute=00, hour=12))
def daily_odm2_sync():
    """
    ODM2 variables are maintained on an external site this synchronizes data to HydroShare for local caching
    """
    ODM2Variable.sync()


@periodic_task(ignore_result=True, run_every=crontab(day_of_month=1))
def monthly_group_membership_requests_cleanup():
    """
    Delete expired and redeemed group membership requests
    """
    two_months_ago = datetime.today() - timedelta(days=60)
    GroupMembershipRequest.objects.filter(my_date__lte=two_months_ago).delete()


@task_postrun.connect
def update_task_notification(sender=None, task_id=None, state=None, retval=None, **kwargs):
    """
    Updates the state of TaskNotification model when a celery task completes
    :param sender:
    :param task_id:
    :param state:
    :param retval:
    :param kwargs:
    :return:
    """
    if state == states.SUCCESS:
        get_or_create_task_notification(task_id, status="completed", payload=retval)
    elif state in states.EXCEPTION_STATES:
        get_or_create_task_notification(task_id, status="failed", payload=retval)
    elif state == states.REVOKED:
        get_or_create_task_notification(task_id, status="aborted", payload=retval)
    else:
        logger.warning("Unhandled task state of {} for {}".format(state, task_id))
