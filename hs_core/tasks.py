"""Define celery tasks for hs_core app."""

import asyncio
import json
import logging
import os
import sys
import time
import traceback
import zipfile
from datetime import date, datetime, timedelta
from xml.etree import ElementTree

import requests
from celery.exceptions import TaskError
from celery.result import states
from celery.schedules import crontab
from celery.signals import task_postrun
from celery.worker.request import Request
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.mail import send_mail
from django.db.models import F, Q
from django.utils import timezone
from rest_framework import status

from celery import Task, shared_task
from django_irods.icommands import SessionException
from django_irods.storage import IrodsStorage
from hs_access_control.models import GroupMembershipRequest
from hs_collection_resource.models import CollectionDeletedResource
from hs_core.enums import (CrossRefSubmissionStatus, CrossRefUpdate,
                           RelationTypes)
from hs_core.hydroshare import (create_empty_resource, current_site_url,
                                set_dirty_bag_flag, utils)
from hs_core.hydroshare.hs_bagit import (create_bag_metadata_files,
                                         create_bagit_files_by_irods)
from hs_core.hydroshare.resource import (deposit_res_metadata_with_crossref,
                                         get_activated_doi, get_crossref_url,
                                         get_resource_doi)
from hs_core.models import BaseResource, ResourceFile, TaskNotification
from hs_core.task_utils import get_or_create_task_notification
from hs_file_types.models import (FileSetLogicalFile, GenericLogicalFile,
                                  GeoFeatureLogicalFile, GeoRasterLogicalFile,
                                  ModelInstanceLogicalFile,
                                  ModelProgramLogicalFile, NetCDFLogicalFile,
                                  RefTimeseriesLogicalFile,
                                  TimeSeriesLogicalFile)
from hs_odm2.models import ODM2Variable
from hydroshare.hydrocelery import app as celery_app
from theme.models import QuotaMessage, User, UserQuota
from theme.utils import get_quota_message

FILE_TYPE_MAP = {"GenericLogicalFile": GenericLogicalFile,
                 "FileSetLogicalFile": FileSetLogicalFile,
                 "GeoRasterLogicalFile": GeoRasterLogicalFile,
                 "NetCDFLogicalFile": NetCDFLogicalFile,
                 "GeoFeatureLogicalFile": GeoFeatureLogicalFile,
                 "RefTimeseriesLogicalFile": RefTimeseriesLogicalFile,
                 "TimeSeriesLogicalFile": TimeSeriesLogicalFile,
                 "ModelProgramLogicalFile": ModelProgramLogicalFile,
                 "ModelInstanceLogicalFile": ModelInstanceLogicalFile
                 }

# Pass 'django' into getLogger instead of __name__
# for celery tasks (as this seems to be the
# only way to successfully log in code executed
# by celery, despite our catch-all handler).
logger = logging.getLogger('django')


class FileOverrideException(Exception):
    def __init__(self, error_message):
        super(FileOverrideException, self).__init__(self, error_message)


class HydroshareRequest(Request):
    '''A Celery custom request to log failures.
    https://docs.celeryq.dev/en/v5.2.7/userguide/tasks.html#requests-and-custom-requests
    '''
    def on_failure(self, exc_info, send_failed_event=True, return_ok=False):
        super(HydroshareRequest, self).on_failure(
            exc_info,
            # always mark failed
            send_failed_event=True,
            return_ok=False
        )
        warning_message = f"Failure detected for task {self.task.name}. Exception: {exc_info}"
        logger.warning(warning_message)
        if not settings.DISABLE_TASK_EMAILS:
            subject = 'Notification of failing Celery task'
            send_mail(subject, warning_message, settings.DEFAULT_FROM_EMAIL, [settings.DEFAULT_FROM_EMAIL])


class HydroshareTask(Task):
    '''Custom Celery Task configured for Hydroshare
    https://docs.celeryq.dev/en/v4.4.7/userguide/tasks.html?#automatic-retry-for-known-exceptions
    '''
    Request = HydroshareRequest
    autoretry_for = (Exception, KeyError)
    retry_kwargs = {'max_retries': 3}
    retry_backoff = True
    retry_backoff_max = 600
    retry_jitter = True


@celery_app.on_after_finalize.connect
def setup_periodic_tasks(sender, **kwargs):
    if (hasattr(settings, 'DISABLE_PERIODIC_TASKS') and settings.DISABLE_PERIODIC_TASKS):
        logger.debug("Periodic tasks are disabled in SETTINGS")
    else:
        # Hourly
        sender.add_periodic_task(crontab(minute=45), manage_task_hourly.s())

        # Daily (times in UTC)
        sender.add_periodic_task(crontab(minute=0, hour=3), nightly_metadata_review_reminder.s())
        sender.add_periodic_task(crontab(minute=30, hour=3), nightly_zips_cleanup.s())
        sender.add_periodic_task(crontab(minute=0, hour=4), daily_odm2_sync.s())
        sender.add_periodic_task(crontab(minute=30, hour=4), daily_innactive_group_requests_cleanup.s())
        sender.add_periodic_task(crontab(minute=0, hour=5), check_geoserver_registrations.s())
        sender.add_periodic_task(crontab(minute=30, hour=5), nightly_repair_resource_files.s())
        sender.add_periodic_task(crontab(minute=0, hour=6), nightly_cache_file_system_metadata.s())
        sender.add_periodic_task(crontab(minute=30, hour=6), nightly_periodic_task_check.s())

        # Weekly
        sender.add_periodic_task(crontab(minute=0, hour=7, day_of_week=1), task_notification_cleanup.s())

        # Monthly
        sender.add_periodic_task(crontab(minute=30, hour=7, day_of_month=1), update_from_geoconnex_task.s())
        sender.add_periodic_task(crontab(minute=0, hour=8, day_of_week=1, day_of_month='1-7'),
                                 send_over_quota_emails.s())
        sender.add_periodic_task(
            crontab(minute=30, hour=8, day_of_month=1), monthly_group_membership_requests_cleanup.s())


# Currently there are two different cleanups scheduled.
# One is 20 minutes after creation, the other is nightly.
# TODO Clean up zipfiles in remote federated storage as well.
@celery_app.task(ignore_result=True, base=HydroshareTask)
def nightly_zips_cleanup():
    # delete 2 days ago
    date_folder = (date.today() - timedelta(2)).strftime('%Y-%m-%d')
    zips_daily_date = "zips/{daily_date}".format(daily_date=date_folder)
    if __debug__:
        logger.debug("cleaning up {}".format(zips_daily_date))
    istorage = IrodsStorage()
    if istorage.exists(zips_daily_date):
        istorage.delete(zips_daily_date)
    federated_prefixes = BaseResource.objects.order_by().values_list('resource_federation_path').distinct()

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


@celery_app.task(ignore_result=True, base=HydroshareTask)
def nightly_periodic_task_check():
    with open("celery/periodic_tasks_last_executed.txt", mode='w') as file:
        file.write(timezone.now().strftime('%m/%d/%y %H:%M:%S'))


@celery_app.task(ignore_result=True, base=HydroshareTask)
def nightly_repair_resource_files():
    """
    Run repair_resource on resources updated in the last day
    """
    from hs_core.management.utils import check_time, repair_resource
    start_time = time.time()
    cuttoff_time = timezone.now() - timedelta(days=1)
    recently_updated_resources = BaseResource.objects \
        .filter(updated__gte=cuttoff_time, raccess__published=False)
    repaired_resources = []
    try:
        for res in recently_updated_resources:
            check_time(start_time, settings.NIGHTLY_RESOURCE_REPAIR_DURATION)
            is_corrupt = False
            try:
                _, missing_django, dangling_in_django = repair_resource(res, logger)
                is_corrupt = missing_django > 0 or dangling_in_django > 0
            except ObjectDoesNotExist:
                logger.info("nightly_repair_resource_files encountered dangling iRods files for a nonexistent resource")
            if is_corrupt:
                repaired_resources.append(res)

        # spend any remaining time fixing resources that haven't been checked
        # followed by those previously checked, prioritizing the oldest checked date
        recently_updated_rids = [res.short_id for res in recently_updated_resources]
        not_recently_updated = BaseResource.objects \
            .exclude(short_id__in=recently_updated_rids) \
            .exclude(raccess__published=True) \
            .order_by(F('files_checked').asc(nulls_first=True))
        for res in not_recently_updated:
            check_time(start_time, settings.NIGHTLY_RESOURCE_REPAIR_DURATION)
            is_corrupt = False
            try:
                _, missing_django, dangling_in_django = repair_resource(res, logger)
                is_corrupt = missing_django > 0 or dangling_in_django > 0
            except ObjectDoesNotExist:
                logger.info("nightly_repair_resource_files encountered dangling iRods files for a nonexistent resource")
            if is_corrupt:
                repaired_resources.append(res)
    except TimeoutError:
        logger.info(f"nightly_repair_resource_files terminated after \
                    {settings.NIGHTLY_RESOURCE_REPAIR_DURATION} seconds")

    if settings.NOTIFY_OWNERS_AFTER_RESOURCE_REPAIR:
        for res in repaired_resources:
            notify_owners_of_resource_repair(res)


@shared_task
def repair_resource_before_publication(res_id):
    """
    Run repair_resource on resource at the initiation of a publication request
    """
    from hs_core.management.utils import repair_resource
    res = utils.get_resource_by_shortkey(res_id)
    if res.raccess.published:
        raise ValidationError("Attempted pre-publication resource repair on a resource that is already published.")
    errors, missing_django, dangling_in_django = repair_resource(res, logger)
    if missing_django > 0 or dangling_in_django > 0:
        res_url = current_site_url() + res.get_absolute_url()

        email_msg = f'''
        <p>We discovered corrupted files in the following resource that is under review for publication:
        <a href="{ res_url }">{ res_url }</a></p>
        <p>We found {missing_django} files missing in Django and {dangling_in_django} files dangling in Django.</p>
        <p>The files issues were fixed automatically. Some logs from the fix are included below:</p>
        <p>{errors}</p>
        '''

        if not settings.DISABLE_TASK_EMAILS:
            send_mail(subject="HydroShare files repaired for resource under publication review",
                      message=email_msg,
                      html_message=email_msg,
                      from_email=settings.DEFAULT_FROM_EMAIL,
                      recipient_list=[settings.DEFAULT_SUPPORT_EMAIL])

    try:
        res.get_crossref_deposit_xml()
    except Exception:
        res_url = current_site_url() + res.get_absolute_url()

        email_msg = f'''
        <p>We were unable to generate Crossref xml in the following resource that is under review for publication:
        <a href="{ res_url }">{ res_url }</a></p>
        <p>Error details:</p>
        <p>{traceback.format_exc()}</p>
        <p>These issues need to be fixed manually. We have notified {settings.DEFAULT_FROM_EMAIL}.</p>
        '''

        if not settings.DISABLE_TASK_EMAILS:
            send_mail(subject="HydroShare metadata contains invalid chars for resource under publication review",
                      message=email_msg,
                      html_message=email_msg,
                      from_email=settings.DEFAULT_FROM_EMAIL,
                      recipient_list=[settings.DEFAULT_SUPPORT_EMAIL, settings.DEFAULT_FROM_EMAIL])


def notify_owners_of_resource_repair(resource):
    """
    Sends email notification to resource owners on resource file repair

    :param resource: a resource that has been repaired
    :return:
    """
    res_url = current_site_url() + resource.get_absolute_url()

    email_msg = f'''Dear Resource Owner,
    <p>We discovered corrupted files in the following resource that you own:
    <a href="{ res_url }">
    { res_url }</a></p>

    <p>File corruption can occur if upload or delete processes get interrupted. The files have been repaired.</p>
    <p>Please contact us if you notice issues or if you repeatedly receive this message.</p>

    <p>Thank you,</p>
    <p>The HydroShare Team</p>
    '''
    if not settings.DISABLE_TASK_EMAILS:
        send_mail(subject="HydroShare resource files repaired",
                  message=email_msg,
                  html_message=email_msg,
                  from_email=settings.DEFAULT_FROM_EMAIL,
                  recipient_list=[o.email for o in resource.raccess.owners.all()])


@celery_app.task(ignore_result=True, base=HydroshareTask)
def manage_task_hourly():
    # The hourly running task do DOI activation check

    # Check DOI activation on failed and pending resources and send email.
    msg_lst = []
    # retrieve all published resources with failed metadata deposition with CrossRef if any and
    # retry metadata deposition - this should check both 'failure' and 'update_failure' flags
    failed_resources = BaseResource.objects.filter(raccess__published=True,
                                                   doi__endswith=CrossRefSubmissionStatus.FAILURE.value)
    for res in failed_resources:
        meta_published_date = res.metadata.dates.all().filter(type='published').first()
        if meta_published_date:
            pub_date = meta_published_date
            pub_date = pub_date.start_date.strftime('%m/%d/%Y')
            act_doi = get_activated_doi(res.doi)
            response = deposit_res_metadata_with_crossref(res)
            if response.status_code == status.HTTP_200_OK:
                # TODO: Pabitra - we are not setting the doi to pending here - the comment below is not correct
                #  should we set it to pending?
                # retry of metadata deposition succeeds, change resource flag from failure
                # to pending
                res.doi = act_doi
                res.save()
                # create bag and compute checksum for published resource to meet DataONE requirement
                create_bag_by_irods(res.short_id)
            else:
                # retry of metadata deposition failed again, notify admin
                if CrossRefSubmissionStatus.UPDATE_FAILURE not in res.doi:
                    # this is the case of retry of initial deposit (deposit when publishing the resource)
                    msg = f"Metadata deposition with CrossRef for the published resource " \
                          f"DOI {act_doi} failed again after retry with first metadata " \
                          f"deposition requested since {pub_date}."
                else:
                    # this is the case of updating crossref metadata deposit as a result of resource metadata change
                    # subsequent to the initial deposit
                    msg = f"Metadata UPDATE deposition with CrossRef for the published resource " \
                          f"DOI {act_doi} failed again after retry."

                msg_lst.append(msg)
                logger.debug(response.content)
        else:
            msg_lst.append("{res_id} does not have published date in its metadata.".format(
                res_id=res.short_id))

    # get all published resources with doi ending with 'pending' or 'update_pending'
    pending_resources = BaseResource.objects.filter(raccess__published=True,
                                                    doi__endswith=CrossRefSubmissionStatus.PENDING.value)
    for res in pending_resources:
        meta_published_date = res.metadata.dates.all().filter(type='published').first()
        if meta_published_date:
            pub_date = meta_published_date
            pub_date = pub_date.start_date.strftime('%m/%d/%Y')
            act_doi = get_activated_doi(res.doi)
            main_url = get_crossref_url()
            req_str = '{MAIN_URL}servlet/submissionDownload?usr={USERNAME}&pwd=' \
                      '{PASSWORD}&doi_batch_id={DOI_BATCH_ID}&type={TYPE}'
            response = requests.get(req_str.format(MAIN_URL=main_url,
                                                   USERNAME=settings.CROSSREF_LOGIN_ID,
                                                   PASSWORD=settings.CROSSREF_LOGIN_PWD,
                                                   DOI_BATCH_ID=res.short_id,
                                                   TYPE='result'),
                                    verify=False)
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
                if CrossRefSubmissionStatus.UPDATE_PENDING not in res.doi:
                    # this is the case of initial deposit when publishing the resource
                    msg = f"Published resource DOI {act_doi} is not yet activated with request " \
                          f"data deposited since {pub_date}."
                else:
                    # this is the case of updating crossref metadata deposit
                    msg = (f"Request to update CrossRef deposit for published resource DOI {act_doi} "
                           f"is still in a pending state.")

                msg_lst.append(msg)
                logger.debug(response.content)
            else:
                notify_owners_of_publication_success(res)
        else:
            msg_lst.append("{res_id} does not have published date in its metadata.".format(
                res_id=res.short_id))

    # get all un-published resources with doi ending in 'pending or 'update_pending'
    pending_unpublished_resources = BaseResource.objects.filter(raccess__published=False,
                                                                doi__endswith=CrossRefSubmissionStatus.PENDING.value)
    for res in pending_unpublished_resources:
        msg_lst.append(f"{res.short_id} has pending in DOI but resource_access shows unpublished. "
                       "This indicates an issue with the resource, please notify a developer")

    if msg_lst and not settings.DISABLE_TASK_EMAILS:
        email_msg = '\n'.join(msg_lst)
        subject = 'Notification of pending DOI deposition/activation of published resources'
        # send email for people monitoring and follow-up as needed
        send_mail(subject, email_msg, settings.DEFAULT_FROM_EMAIL, [settings.DEFAULT_SUPPORT_EMAIL])

    # update crossref deposit for published resource for which relevant metadata has been updated
    # excludes published resources that have either 'pending' or 'update_pending' in doi
    update_deposit_resources = BaseResource.objects \
        .filter(raccess__published=True,
                extra_data__contains={CrossRefUpdate.UPDATE.value: 'True'}) \
        .exclude(doi__endswith=CrossRefSubmissionStatus.PENDING.value)

    for res in update_deposit_resources:
        _update_crossref_deposit(res)
        res.extra_data[CrossRefUpdate.UPDATE.value] = 'False'
        res.save()


@celery_app.task(ignore_result=True, base=HydroshareTask)
def update_from_geoconnex_task():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(utils.update_geoconnex_texts())


@celery_app.task(ignore_result=True, base=HydroshareTask)
def nightly_metadata_review_reminder():
    # The daiy check for resources with active metadata review that has been pending for more than 48hrs

    if settings.DISABLE_TASK_EMAILS:
        return

    pending_resources = BaseResource.objects.filter(raccess__review_pending=True)
    for res in pending_resources:
        review_date = res.metadata.dates.all().filter(type='reviewStarted').first()
        if review_date:
            review_date = review_date.start_date
            cutoff_date = timezone.now() - timedelta(days=2)
            if review_date < cutoff_date:
                res_url = current_site_url() + res.get_absolute_url()
                subject = f"Metadata review pending since " \
                    f"{ review_date.strftime('%m/%d/%Y') } for { res.metadata.title }"
                email_msg = f'''
                Metadata review for <a href="{ res_url }">{ res_url }</a>
                was requested at { review_date.strftime("%Y-%m-%d %H:%M:%S") }.

                This is a reminder to review and approve/reject the publication request.
                '''
                recipients = [settings.DEFAULT_SUPPORT_EMAIL]
                send_mail(subject, email_msg, settings.DEFAULT_FROM_EMAIL, recipients)


def notify_owners_of_publication_success(resource):
    """
    Sends email notification to resource owners on publication success

    :param resource: a resource that has been published
    :return:
    """
    res_url = current_site_url() + resource.get_absolute_url()

    email_msg = f'''Dear Resource Owner,
    <p>The following resource that you submitted for publication:
    <a href="{ res_url }">
    { res_url }</a>
    has been reviewed and determined to meet HydroShare's minimum metadata standards and community guidelines.</p>

    <p>The publication request was processed by <a href="https://www.crossref.org/">Crossref.org</a>.
    The Digital Object Identifier (DOI) for your resource is:
    <a href="{ get_resource_doi(resource.short_id) }">https://doi.org/10.4211/hs.{ resource.short_id }</a></p>

    <p>Thank you,</p>
    <p>The HydroShare Team</p>
    '''
    if not settings.DISABLE_TASK_EMAILS:
        send_mail(subject="HydroShare resource metadata review completed",
                  message=email_msg,
                  html_message=email_msg,
                  from_email=settings.DEFAULT_FROM_EMAIL,
                  recipient_list=[o.email for o in resource.raccess.owners.all()])


@celery_app.task(ignore_result=True, base=HydroshareTask)
def send_over_quota_emails():
    """
    Checks over quota cases and sends quota warning emails as needed.

    This function retrieves the quota message settings and user quotas from the database,
    and sends warning emails to users who have exceeded their quota limits.

    Returns:
        None
    """
    from hs_core.views.utils import get_default_support_user
    hs_internal_zone = "hydroshare"
    if not QuotaMessage.objects.exists():
        QuotaMessage.objects.create()
    qmsg = QuotaMessage.objects.first()
    users = User.objects.filter(is_active=True).filter(is_superuser=False).all()
    for u in users:
        uq = UserQuota.objects.filter(user__username=u.username, zone=hs_internal_zone).first()
        if uq:
            used_percent = uq.used_percent
            today = date.today()
            if used_percent >= qmsg.soft_limit_percent:
                if used_percent >= 100 and used_percent < qmsg.hard_limit_percent:
                    if not uq.grace_period_ends:
                        # triggers grace period counting
                        uq.grace_period_ends = today + timedelta(days=qmsg.grace_period)
                        send_user_notification_at_quota_grace_start(u.pk)
                elif used_percent >= qmsg.hard_limit_percent:
                    # reset grace period to 0 when user quota exceeds hard limit
                    uq.grace_period_ends = None
                uq.save()

                support_user = get_default_support_user()
                msg_str = f'Dear {support_user.first_name}{support_user.last_name}:\n\n'
                msg_str += f'The following user (#{ u.id }) has exceeded their quota:{u.email}\n\n'
                ori_qm = get_quota_message(u)
                msg_str += ori_qm
                subject = f'Quota warning for {u.email}(id#{u.id})'
                if settings.DEBUG or settings.DISABLE_TASK_EMAILS:
                    logger.info("quota warning email not sent out on debug server but logged instead: "
                                "{}".format(msg_str))
                else:
                    try:
                        # send email for people monitoring and follow-up as needed
                        send_mail(subject, '', settings.DEFAULT_FROM_EMAIL,
                                  [settings.DEFAULT_SUPPORT_EMAIL],
                                  html_message=msg_str)
                    except Exception as ex:
                        logger.error("Failed to send quota warning email: " + str(ex))
            else:
                if uq.grace_period_ends and uq.grace_period_ends < today :
                    # reset grace period now that the user is below quota soft limit
                    uq.grace_period_ends = None
                    uq.save()
        else:
            logger.debug('user ' + u.username + ' does not have UserQuota foreign key relation')


@celery_app.task(ignore_result=True, base=HydroshareTask)
def send_user_notification_at_quota_grace_start(user_pk):
    u = User.objects.get(pk=user_pk)
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
    msg_str += ori_qm

    msg_str += '\n\nHydroShare Support'
    subject = 'Quota warning'
    if settings.DEBUG or settings.DISABLE_TASK_EMAILS:
        logger.info("quota warning email not sent out on debug server but logged instead: "
                    "{}".format(msg_str))
    else:
        try:
            # send email for people monitoring and follow-up as needed
            send_mail(subject, '', settings.DEFAULT_FROM_EMAIL,
                      [u.email],
                      html_message=msg_str)
        except Exception as ex:
            logger.debug("Failed to send quota warning email: " + str(ex))


@celery_app.task(ignore_result=True, base=HydroshareTask)
def check_geoserver_registrations(resources, run_async=True):
    # Check to ensure resources have updated web services registrations

    DISTRIBUTE_WEB_REGISTRATIONS_OVER = 2  # hours

    if not settings.HSWS_ACTIVATED:
        return

    if not resources:
        cuttoff_time = timezone.now() - timedelta(days=1)
        resources = BaseResource.objects.filter(updated__gte=cuttoff_time, raccess__public=True)

    if run_async:
        # Evenly distribute requests
        delay_between_res = (DISTRIBUTE_WEB_REGISTRATIONS_OVER * 60 * 60) / resources.count()

        for current_res_num, res in enumerate(resources, start=0):
            delay = delay_between_res * current_res_num
            update_web_services.apply_async((
                settings.HSWS_URL,
                settings.HSWS_API_TOKEN,
                settings.HSWS_TIMEOUT,
                settings.HSWS_PUBLISH_URLS,
                res.short_id
            ), countdown=delay)
    else:
        failed_resources = {}
        for res in resources:
            response = update_web_services(
                settings.HSWS_URL,
                settings.HSWS_API_TOKEN,
                settings.HSWS_TIMEOUT,
                settings.HSWS_PUBLISH_URLS,
                res.short_id
            )
            if not response['success']:
                res_url = current_site_url() + res.get_absolute_url()
                failed_resources[res_url] = response
        if failed_resources:
            err_msg = 'Attempt to update web services failed for the following resources:\n'
            for res_url, resp in failed_resources:
                err_msg += f'{res_url} => {json.dumps(resp)}\n'
            if not settings.DISABLE_TASK_EMAILS:
                subject = "Web services failed to update"
                recipients = [settings.DEFAULT_SUPPORT_EMAIL]
                send_mail(subject, err_msg, settings.DEFAULT_FROM_EMAIL, recipients)
            else:
                logger.error(err_msg)
            raise TaskError(err_msg)


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
        resource.save(update_fields=['file_unpack_status'])

        resource_files = []
        for i, f in enumerate(files):
            logger.debug("Adding file {0} to resource {1}".format(f.name, pk))
            res_file = utils.add_file_to_resource(resource, f, save_file_system_metadata=False)
            res_file.set_system_metadata(resource=resource, save=False)
            resource_files.append(res_file)
            resource.file_unpack_message = "Imported {0} of about {1} file(s) ...".format(
                i, num_files)
            resource.save(update_fields=['file_unpack_message'])

        ResourceFile.objects.bulk_update(resource_files, ResourceFile.system_meta_fields(),
                                         batch_size=settings.BULK_UPDATE_CREATE_BATCH_SIZE)

        # This might make the resource unsuitable for public consumption
        resource.update_public_and_discoverable()
        # TODO: this is a bit of a lie because a different user requested the bag overwrite
        utils.resource_modified(resource, resource.creator, overwrite_bag=False)

        # Call success callback
        resource.file_unpack_message = None
        resource.file_unpack_status = 'Done'
        resource.save(update_fields=['file_unpack_message', 'file_unpack_status'])

    except BaseResource.DoesNotExist:
        msg = "Unable to add zip file contents to non-existent resource {pk}."
        msg = msg.format(pk=pk)
        logger.error(msg)
    except: # noqa
        exc_info = "".join(traceback.format_exception(*sys.exc_info()))
        if resource:
            resource.file_unpack_status = 'Error'
            resource.file_unpack_message = exc_info
            resource.save(update_fields=['file_unpack_status', 'file_unpack_message'])

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
            res.create_aggregation_meta_files(path=short_path)
        else:  # all metadata included, e.g., /data/*
            res.create_aggregation_meta_files()

    if aggregation or sf_zip:
        # input path points to single file aggregation
        # ensure that foo.zip contains aggregation metadata
        # by copying these into a temp subdirectory foo/foo parallel to where foo.zip is stored
        temp_folder_name, ext = os.path.splitext(output_path)  # strip zip to get scratch dir
        head, tail = os.path.split(temp_folder_name)  # tail is unqualified folder name "foo"
        out_with_folder = os.path.join(temp_folder_name, tail)  # foo/foo is subdir to zip
        # in the case of user provided zip file name, out_with_folder path may not end with
        # aggregation file name
        aggr_filename = os.path.basename(input_path)
        if not out_with_folder.endswith(aggr_filename):
            out_with_folder = os.path.join(os.path.dirname(out_with_folder), aggr_filename)
        istorage.copyFiles(input_path, out_with_folder)
        if not aggregation:
            if '/data/contents/' in input_path:
                short_path = input_path.split('/data/contents/')[1]  # strip /data/contents/
            else:
                short_path = input_path
            try:
                aggregation = res.get_aggregation_by_name(short_path)
            except ObjectDoesNotExist:
                pass

        if aggregation:
            try:
                istorage.copyFiles(aggregation.map_file_path, temp_folder_name)
            except SessionException:
                logger.error("cannot copy {}".format(aggregation.map_file_path))
            try:
                istorage.copyFiles(aggregation.metadata_file_path, temp_folder_name)
            except SessionException:
                logger.error("cannot copy {}".format(aggregation.metadata_file_path))
            if aggregation.is_model_program or aggregation.is_model_instance:
                try:
                    istorage.copyFiles(aggregation.schema_file_path, temp_folder_name)
                except SessionException:
                    logger.error("cannot copy {}".format(aggregation.schema_file_path))
                if aggregation.is_model_instance:
                    try:
                        istorage.copyFiles(aggregation.schema_values_file_path, temp_folder_name)
                    except SessionException:
                        logger.error("cannot copy {}".format(aggregation.schema_values_file_path))
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
def create_bag_by_irods(resource_id, create_zip=True):
    """Create a resource bag on iRODS side by running the bagit rule and ibun zip.
    This function runs as a celery task, invoked asynchronously so that it does not
    block the main web thread when it creates bags for very large files which will take some time.
    :param
    resource_id: the resource uuid that is used to look for the resource to create the bag for.
    :param create_zip: defaults to True, set to false to create bagit files without zipping
    :return: bag_url if bag creation operation succeeds or
             raise an exception if resource does not exist or any other issues that prevent bags from being created.
    """
    res = utils.get_resource_by_shortkey(resource_id)

    istorage = res.get_irods_storage()

    bag_path = res.bag_path

    metadata_dirty = res.getAVU('metadata_dirty')
    metadata_dirty = metadata_dirty is None or metadata_dirty
    # if metadata has been changed, then regenerate metadata xml files
    if metadata_dirty:
        create_bag_metadata_files(res)

    bag_modified = res.getAVU("bag_modified")
    bag_modified = bag_modified is None or bag_modified
    if metadata_dirty or bag_modified:
        create_bagit_files_by_irods(res, istorage)

    if create_zip:
        irods_bagit_input_path = res.get_irods_path(resource_id, prepend_short_id=False)

        # only proceed when the resource is not deleted potentially by another request
        # when being downloaded
        is_exist = istorage.exists(irods_bagit_input_path)
        if is_exist:
            try:
                if istorage.exists(bag_path):
                    istorage.delete(bag_path)
                istorage.zipup(irods_bagit_input_path, bag_path)
                if res.raccess.published:
                    # compute checksum to meet DataONE distribution requirement
                    chksum = istorage.checksum(bag_path)
                    res.bag_checksum = chksum
                res.setAVU("bag_modified", False)
                return res.bag_url
            except SessionException as ex:
                raise SessionException(-1, '', ex.stderr)
        else:
            raise ObjectDoesNotExist('Resource {} does not exist.'.format(resource_id))


@shared_task
def copy_resource_task(ori_res_id, new_res_id=None, request_username=None):
    new_res = None
    try:
        if not new_res_id:
            new_res = create_empty_resource(ori_res_id, request_username, action='copy')
            new_res_id = new_res.short_id
        utils.copy_resource_files_and_AVUs(ori_res_id, new_res_id)
        ori_res = utils.get_resource_by_shortkey(ori_res_id)
        if not new_res:
            new_res = utils.get_resource_by_shortkey(new_res_id)
        utils.copy_and_create_metadata(ori_res, new_res)

        # the resource to be copied is a versioned resource, need to delete this isVersionOf
        # relation element to maintain the single versioning obsolescence chain
        new_res.metadata.relations.all().filter(type=RelationTypes.isVersionOf).delete()

        # create the relation element for the new_res
        today = date.today().strftime("%m/%d/%Y")
        derived_from = "{}, accessed on: {}".format(ori_res.get_citation(), today)
        # since we are allowing user to add relation of type source, need to check we don't already have it
        if not new_res.metadata.relations.all().filter(type=RelationTypes.source, value=derived_from).exists():
            new_res.metadata.create_element('relation', type=RelationTypes.source, value=derived_from)

        if ori_res.resource_type.lower() == "collectionresource":
            # clone contained_res list of original collection and add to new collection
            # note that new collection will not contain "deleted resources"
            new_res.resources.set(ori_res.resources.all())

        utils.set_dirty_bag_flag(new_res)
        return new_res.absolute_url
    except Exception as ex:
        if new_res:
            new_res.delete()
        raise utils.ResourceCopyException(str(ex))


@shared_task
def create_new_version_resource_task(ori_res_id, username, new_res_id=None):
    """
    Task for creating a new version of a resource
    Args:
        ori_res_id: the original resource id that is to be versioned.
        new_res_id: the new versioned resource id from the original resource. If None, a
        new resource will be created.
        username: the requesting user's username
    Returns:
        the new versioned resource url as the payload
    """
    try:
        ori_res = utils.get_resource_by_shortkey(ori_res_id)
        new_res = None
        if not new_res_id:
            new_res = create_empty_resource(ori_res_id, username)
            new_res_id = new_res.short_id
        utils.copy_resource_files_and_AVUs(ori_res_id, new_res_id)

        # copy metadata from source resource to target new-versioned resource except three elements
        if not new_res:
            new_res = utils.get_resource_by_shortkey(new_res_id)
        utils.copy_and_create_metadata(ori_res, new_res)

        # add or update Relation element to link source and target resources
        ori_res.metadata.create_element('relation', type=RelationTypes.isReplacedBy, value=new_res.get_citation())

        # the original resource is already a versioned resource, and its isVersionOf relation
        # element is copied over to this new version resource, needs to delete this element so
        # it can be created to link to its original resource correctly
        new_res.metadata.relations.all().filter(type=RelationTypes.isVersionOf).delete()

        new_res.metadata.create_element('relation', type=RelationTypes.isVersionOf, value=ori_res.get_citation())

        if ori_res.resource_type.lower() == "collectionresource":
            # clone contained_res list of original collection and add to new collection
            # note that new version collection will not contain "deleted resources"
            ori_resources = ori_res.resources.all()
            new_res.resources.set(ori_resources)
            # set the isPartOf metadata on all of the contained resources so that they also point at the new col
            for res in ori_resources:
                res.metadata.create_element('relation', type=RelationTypes.isPartOf, value=new_res.get_citation())

        # since an isReplaceBy relation element is added to original resource, needs to call
        # resource_modified() for original resource
        # if everything goes well up to this point, set original resource to be immutable so that
        # obsoleted resources cannot be modified from REST API
        ori_res.raccess.immutable = True
        ori_res.raccess.save()
        ori_res.save()
        utils.set_dirty_bag_flag(new_res)
        return new_res.absolute_url
    except Exception as ex:
        if new_res:
            new_res.delete()
        raise utils.ResourceVersioningException(str(ex))
    finally:
        # release the lock regardless
        ori_res.locked_time = None
        ori_res.save()


@shared_task
def replicate_resource_bag_to_user_zone_task(res_id, request_username):
    """
    Task for replicating resource bag which will be created on demand if not existent already to iRODS user zone
    Args:
        res_id: the resource id with its bag to be replicated to iRODS user zone
        request_username: the requesting user's username to whose user zone space the bag is copied to

    Returns:
    None, but exceptions will be raised if there is an issue with iRODS operation
    """

    res = utils.get_resource_by_shortkey(res_id)
    res_coll = res.root_path
    istorage = res.get_irods_storage()
    if istorage.exists(res_coll):
        bag_modified = res.getAVU('bag_modified')
        if bag_modified is None or not bag_modified:
            if not istorage.exists(res.bag_path):
                create_bag_by_irods(res_id)
        else:
            create_bag_by_irods(res_id)

        # do replication of the resource bag to irods user zone
        if not res.resource_federation_path:
            istorage.set_fed_zone_session()
        src_file = res.bag_path
        tgt_file = '/{userzone}/home/{username}/{resid}.zip'.format(
            userzone=settings.HS_USER_IRODS_ZONE, username=request_username, resid=res_id)
        fsize = istorage.size(src_file)
        utils.validate_user_quota(request_username, fsize)
        istorage.copyFiles(src_file, tgt_file)
        return None
    else:
        raise ValidationError("Resource {} does not exist in iRODS".format(res.short_id))


@shared_task
def delete_resource_task(resource_id, request_username=None):
    """
    Deletes a resource managed by HydroShare. The caller must be an owner of the resource or an
    administrator to perform this function.
    :param resource_id: The unique HydroShare identifier of the resource to be deleted
    :return: resource_id if delete operation succeeds
             raise an exception if there were errors.
    """
    res = utils.get_resource_by_shortkey(resource_id)
    res_title = res.metadata.title
    res_type = res.resource_type
    resource_related_collections = [col for col in res.collections.all()]
    owners_list = [owner for owner in res.raccess.owners.all()]

    # when the most recent version of a resource in an obsolescence chain is deleted, the previous
    # version in the chain needs to be set as the "active" version by deleting "isReplacedBy"
    # relation element
    relation_is_version_of = res.metadata.relations.all().filter(type=RelationTypes.isVersionOf).first()
    if relation_is_version_of:
        is_version_of_res_link = relation_is_version_of.value
        idx = is_version_of_res_link.rindex('/')
        if idx == -1:
            obsolete_res_id = is_version_of_res_link
        else:
            obsolete_res_id = is_version_of_res_link[idx + 1:]
        obsolete_res = utils.get_resource_by_shortkey(obsolete_res_id)
        relation_is_replaced_by = obsolete_res.metadata.relations.all().filter(type=RelationTypes.isReplacedBy).first()
        if relation_is_replaced_by:
            eid = relation_is_replaced_by.id
            obsolete_res.metadata.delete_element('relation', eid)
            # also make this obsoleted resource editable if not published now that it becomes the latest version
            if not obsolete_res.raccess.published:
                obsolete_res.raccess.immutable = False
                obsolete_res.raccess.save()

    for res_in_col in res.resources.all():
        # res being deleted is a collection resource - delete isPartOf relation of all resources that are part of the
        # collection
        if res_in_col.metadata.relations.filter(type='isPartOf', value__endswith=res.short_id).exists():
            res_in_col.metadata.relations.filter(type='isPartOf', value__endswith=res.short_id).delete()
            set_dirty_bag_flag(res_in_col)

    for collection_res in resource_related_collections:
        # res being deleted is part of one or more collections - delete hasPart relation for all those collections
        collection_res.metadata.relations.filter(type='hasPart', value__endswith=res.short_id).delete()
        set_dirty_bag_flag(collection_res)

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

    # return the page URL to redirect to after resource deletion task is complete
    return '/my-resources/'


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
            resource = utils.get_resource_by_shortkey(res_id)
            response_content = json.loads(response.content.decode())
            if "resource" in response_content:
                for key, value in response_content["resource"].items():
                    resource.extra_metadata[key] = value
                    resource.save()

            if "content" in response_content:
                for url in response_content["content"]:
                    logical_files = list(resource.logical_files)
                    lf = logical_files[[i.aggregation_name for i in
                                        logical_files].index(
                        url["layer_name"].encode()
                    )]
                    lf.metadata.extra_metadata["Web Services URL"] = url["message"]
                    lf.metadata.save()
        if status.is_success(response.status_code):
            return response.json()
        else:
            response.raise_for_status()
    except Exception as e:
        logger.error(f"Error updating web services: {str(e)}")
        raise


@shared_task
def resource_debug(resource_id):
    """Update web services hosted by GeoServer and HydroServer.
    """
    resource = utils.get_resource_by_shortkey(resource_id)
    from hs_core.management.utils import check_irods_files
    return check_irods_files(resource, log_errors=False, return_errors=True)


@shared_task
def get_non_preferred_paths(resource_id):
    """Gets a list of file/folder paths that contain non-preferred characters"""

    resource = utils.get_resource_by_shortkey(resource_id)
    non_preferred_paths = []

    if resource.resource_type == "CompositeResource":
        non_preferred_paths = resource.get_non_preferred_path_names()
    return non_preferred_paths


@shared_task
def unzip_task(user_pk, res_id, zip_with_rel_path, bool_remove_original, overwrite=False, auto_aggregate=False,
               ingest_metadata=False, unzip_to_folder=False):
    from hs_core.views.utils import unzip_file
    user = User.objects.get(pk=user_pk)
    unzip_file(user, res_id, zip_with_rel_path, bool_remove_original, overwrite, auto_aggregate, ingest_metadata,
               unzip_to_folder)


@shared_task
def move_aggregation_task(res_id, file_type_id, file_type, tgt_path):
    from hs_core.views.utils import rename_irods_file_or_folder_in_django
    res = utils.get_resource_by_shortkey(res_id)
    istorage = res.get_irods_storage()
    res_files = []
    file_type_obj = FILE_TYPE_MAP[file_type]
    aggregation = file_type_obj.objects.get(id=file_type_id)
    res_files.extend(aggregation.files.all())
    orig_aggregation_name = aggregation.aggregation_name
    tgt_path = tgt_path.strip()
    for file in res_files:
        if tgt_path:
            tgt_full_path = os.path.join(res.file_path, tgt_path, os.path.basename(file.storage_path))
        else:
            tgt_full_path = os.path.join(res.file_path, os.path.basename(file.storage_path))

        istorage.moveFile(file.storage_path, tgt_full_path)
        rename_irods_file_or_folder_in_django(res, file.storage_path, tgt_full_path)
    if tgt_path:
        new_aggregation_name = os.path.join(tgt_path, os.path.basename(orig_aggregation_name))
    else:
        new_aggregation_name = os.path.basename(orig_aggregation_name)

    res.set_flag_to_recreate_aggregation_meta_files(orig_path=orig_aggregation_name,
                                                    new_path=new_aggregation_name)
    return res.get_absolute_url()


@shared_task
def set_resource_files_system_metadata(resource_id):
    """
    Sets size, checksum, and modified time for resource files by getting these values
    from iRODS and stores in db
    :param resource_id: the id of the resource for which to set system metadata for all files currently missing
    these metadata in db
    """
    resource = utils.get_resource_by_shortkey(resource_id)
    res_files = resource.files.exclude(_size__gte=0).all()
    for res_file in res_files:
        res_file.set_system_metadata(resource=resource, save=False)

    ResourceFile.objects.bulk_update(res_files, ResourceFile.system_meta_fields(),
                                     batch_size=settings.BULK_UPDATE_CREATE_BATCH_SIZE)


@celery_app.task(ignore_result=True, base=HydroshareTask)
def nightly_cache_file_system_metadata():
    """
    Generate and store file checksums and modified times for a subset of resources
    """
    from hs_core.management.utils import check_time

    def set_res_files_system_metadata(resource):
        # exclude files with size 0 (file missing in irods)
        res_files = resource.files.filter(
            Q(_checksum__isnull=True)
            | Q(_modified_time__isnull=True)
            | Q(_size__lt=0)).exclude(_size=0).all()
        for res_file in res_files:
            res_file.set_system_metadata(resource=resource, save=False)

        ResourceFile.objects.bulk_update(res_files, ResourceFile.system_meta_fields(),
                                         batch_size=settings.BULK_UPDATE_CREATE_BATCH_SIZE)
    start_time = time.time()
    cuttoff_time = timezone.now() - timedelta(days=1)
    recently_updated_resources = BaseResource.objects \
        .filter(updated__gte=cuttoff_time)
    try:
        for res in recently_updated_resources:
            check_time(start_time, settings.NIGHTLY_GENERATE_FILESYSTEM_METADATA_DURATION)
            set_res_files_system_metadata(res)

        # spend any remaining time generating filesystem metadata starting with most recently edited resources
        recently_updated_rids = [res.short_id for res in recently_updated_resources]
        less_recently_updated = BaseResource.objects \
            .exclude(short_id__in=recently_updated_rids) \
            .order_by('-updated')
        for res in less_recently_updated:
            check_time(start_time, settings.NIGHTLY_GENERATE_FILESYSTEM_METADATA_DURATION)
            set_res_files_system_metadata(res)
    except TimeoutError:
        logger.info(f"nightly_cache_file_system_metadata terminated after \
                    {settings.NIGHTLY_GENERATE_FILESYSTEM_METADATA_DURATION} seconds")


@celery_app.task(ignore_result=True, base=HydroshareTask)
def daily_odm2_sync():
    """
    ODM2 variables are maintained on an external site this synchronizes data to HydroShare for local caching
    """
    ODM2Variable.sync()


@celery_app.task(ignore_result=True, base=HydroshareTask)
def monthly_group_membership_requests_cleanup():
    """
    Delete expired and redeemed group membership requests
    """
    two_months_ago = datetime.today() - timedelta(days=60)
    GroupMembershipRequest.objects.filter(date_requested__lte=two_months_ago).delete()


@celery_app.task(ignore_result=True, base=HydroshareTask)
def daily_innactive_group_requests_cleanup():
    """
    Redeem group membership requests for innactive users
    """
    GroupMembershipRequest.objects.filter(request_from__is_active=False).update(redeemed=True)
    GroupMembershipRequest.objects.filter(invitation_to__is_active=False).update(redeemed=True)


@task_postrun.connect
def update_task_notification(sender=None, task_id=None, task=None, state=None, retval=None, **kwargs):
    """
    Updates the state of TaskNotification model when a celery task completes
    :param sender:
    :param task_id: task id
    :param task: task object
    :param state: task return state
    :param retval: task return value
    :param kwargs:
    :return:
    """
    if task.name in settings.TASK_NAME_LIST:
        if state == states.SUCCESS:
            get_or_create_task_notification(task_id, status="completed", payload=retval)
        elif state in states.EXCEPTION_STATES:
            get_or_create_task_notification(task_id, status="failed", payload=retval)
        elif state == states.REVOKED:
            get_or_create_task_notification(task_id, status="aborted", payload=retval)
        else:
            logger.warning("Unhandled task state of {} for {}".format(state, task_id))


@celery_app.task(ignore_result=True, base=HydroshareTask)
def task_notification_cleanup():
    """
    Delete expired task notifications each week
    """
    week_ago = datetime.today() - timedelta(days=7)
    TaskNotification.objects.filter(created__lte=week_ago).delete()


@shared_task
def update_crossref_meta_deposit(res_id):
    """
    Update the metadata deposit for a published resource with Crossref
    """
    resource = utils.get_resource_by_shortkey(res_id)
    if not resource.raccess.published:
        raise ValidationError("Resource {} is not a published resource".format(res_id))
    _update_crossref_deposit(resource)


def _update_crossref_deposit(resource):
    logger.info(f"Updating Crossref metadata deposit for published resource: {resource.short_id}")
    resource.doi = get_resource_doi(resource.short_id, CrossRefSubmissionStatus.UPDATE_PENDING)
    resource.save()
    response = deposit_res_metadata_with_crossref(resource)
    if not response.status_code == status.HTTP_200_OK:
        # resource metadata deposition failed from CrossRef - set failure flag to be retried in a
        # crontab celery task
        err_msg = (f"Received a {response.status_code} from Crossref while updating "
                   f"metadata for published resource: {resource.short_id}")
        logger.error(err_msg)
        resource.doi = get_resource_doi(resource.short_id, CrossRefSubmissionStatus.UPDATE_FAILURE)
        resource.save()
