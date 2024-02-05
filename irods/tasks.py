"""Define celery tasks for irods app."""

import json
import logging
from datetime import date, timedelta

from celery.schedules import crontab
from celery.worker.request import Request
from django.conf import settings
from django.core.mail import send_mail

from celery import Task
from hs_core.views.utils import run_ssh_command
from hydroshare.hydrocelery import app as celery_app
from theme.models import QuotaMessage, User, UserQuota
from theme.utils import get_quota_message


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
        # Monthly
        sender.add_periodic_task(crontab(minute=0, hour=8, day_of_week=1, day_of_month='1-7'),
                                 send_over_quota_emails.s())


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
                    toggle_userzone_upload(user_pk=u.pk, allow_upload=False)
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
                    toggle_userzone_upload(user_pk=u.pk, allow_upload=True)
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
def toggle_userzone_upload(user_pk, allow_upload=True):
    """
    Toggles the upload permission for a user in the iRODS user zone.

    Args:
        user_pk (int): The primary key of the user.
        allow_upload (bool, optional): Whether to allow or disable upload. Defaults to True.

    Returns:
        str: JSON-encoded string containing the success message if the operation is successful,
             otherwise an error message.

    Raises:
        Exception: If an error occurs while toggling the upload permission.
    """
    try:
        user = User.objects.get(pk=user_pk)
        if allow_upload:
            script = settings.LINUX_ADMIN_USER_ENABLE_UPLOAD_IN_USER_ZONE_CMD
        else:
            script = settings.LINUX_ADMIN_USER_DISABLE_UPLOAD_IN_USER_ZONE_CMD
        exec_cmd = "{0} {1}".format(
            script,
            user.username,
        )
        output = run_ssh_command(
            host=settings.HS_USER_ZONE_HOST,
            uname=settings.LINUX_ADMIN_USER_FOR_HS_USER_ZONE,
            pwd=settings.LINUX_ADMIN_USER_PWD_FOR_HS_USER_ZONE,
            exec_cmd=exec_cmd,
        )
        for out_str in output:
            if "bash:" in out_str or (
                "ERROR:" in out_str.upper()
                and "CATALOG_ALREADY_HAS_ITEM_BY_THAT_NAME" not in out_str.upper()
            ):
                # there is an error from icommand run which is not about the fact
                # that the user already exists, report the error
                return json.dumps(
                    {
                        "error": "iRODS server failed to create this iRODS account {0}. "
                        "If this issue persists, please notify help@cuahsi.org.".format(
                            user.username
                        )
                    },
                )

        message = f"iRODS upload for user {user.username} was"
        if allow_upload:
            message += " enabled successfully"
        else:
            message += " disabled successfully"
        return json.dumps(
            {
                "success": message,
            },
        )
    except Exception as ex:
        return json.dumps(
            {
                "error": str(ex)
                + " - iRODS server failed to take action on userzone for user {user.username}."
            },
        )
