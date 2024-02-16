import os
from uuid import uuid4
from datetime import date
from django.core.mail import send_mail
from mezzanine.conf import settings
from .enums import QuotaStatus

import logging
logger = logging.getLogger(__name__)


def _get_upload_path(folder_name, name, filename):
    """
    get upload path for pictures uploaded for UserProfile, GroupAccess, and Community models
    to make sure the file name is unique
    :param folder_name: folder name to put file in
    :param name: instance name to uniquely identify a user profile, community, or group
    :param filename: uploaded file name
    :return: the upload path to be used for the ImageField in UserProfile, GroupAccess and Community models
    """
    file_base, file_ext = os.path.splitext(filename)
    unique_id = uuid4().hex
    return f'{folder_name}/{file_base}_{name}_{unique_id}{file_ext}'


def get_upload_path_community(instance, filename):
    return _get_upload_path('community', instance.name, filename)


def get_upload_path_group(instance, filename):
    return _get_upload_path('group', instance.group.name, filename)


def get_upload_path_userprofile(instance, filename):
    return _get_upload_path('profile', instance.user.username, filename)


def get_quota_message(user, quota_data=None):
    """
    get quota warning, grace period, or enforcement message to email users and display
    when the user logins in and display on user profile page
    :param user: The User instance
    :param quota_data: dictionary containing quota data
    :return: quota message string
    """
    return_msg = ''
    uq = user.quotas.filter(zone='hydroshare').first()
    if not quota_data:
        quota_data = get_quota_data(uq)
    qmsg = quota_data["qmsg"]
    allocated = quota_data["allocated"]
    used = quota_data["used"]
    grace = quota_data["grace_period_ends"]
    quota_status = quota_data["status"]
    percent = used * 100.0 / allocated
    rounded_percent = round(percent, 2)
    rounded_used_val = round(used, 4)

    if quota_status == QuotaStatus.GRACE_PERIOD:
        # return quota enforcement message
        msg_template_str = f'{qmsg.enforce_content_prepend} {qmsg.content}\n'
        return_msg += msg_template_str.format(used=rounded_used_val,
                                              unit=uq.unit,
                                              allocated=uq.allocated_value,
                                              zone=uq.zone,
                                              percent=rounded_percent)
    elif quota_status == QuotaStatus.ENFORCEMENT:
        # return quota grace period message
        msg_template_str = f'{qmsg.grace_period_content_prepend} {qmsg.content}\n'
        return_msg += msg_template_str.format(used=rounded_used_val,
                                              unit=uq.unit,
                                              allocated=uq.allocated_value,
                                              zone=uq.zone,
                                              percent=rounded_percent,
                                              cut_off_date=grace)
    elif quota_status == QuotaStatus.WARNING:
        # return quota warning message
        msg_template_str = f'{qmsg.warning_content_prepend} {qmsg.content}\n'
        return_msg += msg_template_str.format(used=rounded_used_val,
                                              unit=uq.unit,
                                              allocated=uq.allocated_value,
                                              zone=uq.zone,
                                              percent=rounded_percent)
    else:
        # return quota informational message
        return_msg += qmsg.warning_content_prepend.format(allocated=uq.allocated_value,
                                                          unit=uq.unit,
                                                          used=rounded_used_val,
                                                          zone=uq.zone,
                                                          percent=rounded_percent)
    return return_msg


def get_quota_data(uq):
    """
    get user quota data for display on user profile page
    :param uq: UserQuota instance
    :return: dictionary containing quota data

    Note that percents are in the range 0 to 100
    """
    from theme.models import QuotaMessage
    if not QuotaMessage.objects.exists():
        QuotaMessage.objects.create()
    qmsg = QuotaMessage.objects.first()
    enforce_quota = qmsg.enforce_quota
    soft_limit = qmsg.soft_limit_percent
    hard_limit = qmsg.hard_limit_percent
    today = date.today()
    grace = uq.grace_period_ends
    allocated = uq.allocated_value
    unit = uq.unit
    uz, dz = uq.get_used_value_by_zone()
    used = uz + dz
    uzp = uz * 100.0 / allocated
    dzp = dz * 100.0 / allocated
    percent = used * 100.0 / allocated
    remaining = allocated - used

    # initiate grace_period counting if not already started by the daily celery task
    if percent >= 100 and not grace:
        # This would indicate that the grace period has not been set even though the user went over quota.
        # This should not happen.
        logger.error(f"User {uq.user.username} went over quota but grace period was not set.")
        status = QuotaStatus.GRACE_PERIOD

    if percent >= hard_limit or (percent >= 100 and grace <= today):
        status = QuotaStatus.ENFORCEMENT
    elif percent >= 100 and grace > today:
        status = QuotaStatus.GRACE_PERIOD
    elif percent >= soft_limit:
        status = QuotaStatus.WARNING
    else:
        status = QuotaStatus.INFO

    uq_data = {"used": used,
               "allocated": allocated,
               "unit": unit,
               "uz": uz,
               "dz": dz,
               "uz_percent": uzp if uzp < 100 else 100,
               "dz_percent": dzp if dzp < 100 else 100,
               "percent": percent if percent < 100 else 100,
               "remaining": 0 if remaining < 0 else remaining,
               "percent_over": 0 if percent < 100 else percent - 100,
               "grace_period_ends": grace,
               "enforce_quota": enforce_quota,
               "status": status,
               "qmsg": qmsg,
               }
    return uq_data


def notify_user_of_quota_action(quota_request, send_on_deny=False):
    """
    Sends email notification to user on approval/denial of thie quota request

    :param quota_request: the quota_request object
    :param send_on_deny: whether emails should be sent on denial. default is to only send emails on quota approval
    :return:
    """

    if quota_request.status != 'approved' and not send_on_deny:
        return

    date = quota_request.date_requested.strftime("%m/%d/%Y, %H:%M:%S")
    email_msg = f'''Dear Hydroshare User,
    <p>On { date }, you requested { quota_request.storage } GB increase in quota.</p>
    <p>Here is the justification you provided: <strong>'{ quota_request.justification }'</strong></p>

    <p>Your request for Quota increase has been reviewed and { quota_request.status }.</p>

    <p>Thank you,</p>
    <p>The HydroShare Team</p>
    '''
    send_mail(subject="HydroShare resource metadata review completed",
              message=email_msg,
              html_message=email_msg,
              from_email=settings.DEFAULT_FROM_EMAIL,
              recipient_list=[quota_request.request_from.email])
