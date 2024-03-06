import os
from uuid import uuid4
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
        quota_data = uq.get_quota_data()
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


def notify_user_of_quota_action(quota_request, send_on_deny=False):
    """
    Sends email notification to user on approval/denial of thie quota request

    :param quota_request: an instance of QuotaRequest
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
    send_mail(subject=f"HydroShare request for Quota increase { quota_request.status }",
              message=email_msg,
              html_message=email_msg,
              from_email=settings.DEFAULT_FROM_EMAIL,
              recipient_list=[quota_request.request_from.email])
