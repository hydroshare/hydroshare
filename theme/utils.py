import os
from uuid import uuid4
from datetime import date, timedelta
from django.core.mail import send_mail
from mezzanine.conf import settings


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


def get_quota_message(user):
    """
    get quota warning, grace period, or enforcement message to email users and display
    when the user logins in and display on user profile page
    :param user: The User instance
    :return: quota message string
    """
    from theme.models import QuotaMessage
    from irods.tasks import send_user_notification_at_quota_grace_start
    if not QuotaMessage.objects.exists():
        QuotaMessage.objects.create()
    qmsg = QuotaMessage.objects.first()
    soft_limit = qmsg.soft_limit_percent
    hard_limit = qmsg.hard_limit_percent
    return_msg = ''
    for uq in user.quotas.all():
        allocated = uq.allocated_value
        uz, dz = uq.get_used_value_by_zone()
        used = uz + dz
        percent = used * 100.0 / allocated
        rounded_percent = round(percent, 2)
        rounded_used_val = round(used, 4)
        today = date.today()
        grace = uq.grace_period_ends

        # initiate grace_period counting if not already started by the daily celery task
        if percent >= 100 and not grace:
            grace = today + timedelta(days=qmsg.grace_period)
            uq.grace_period_ends = grace
            uq.save()
            send_user_notification_at_quota_grace_start.apply_async((user.pk,))

        if percent >= hard_limit or (percent >= 100 and grace <= today):
            # return quota enforcement message
            msg_template_str = f'{qmsg.enforce_content_prepend} {qmsg.content}\n'
            return_msg += msg_template_str.format(used=rounded_used_val,
                                                  unit=uq.unit,
                                                  allocated=uq.allocated_value,
                                                  zone=uq.zone,
                                                  percent=rounded_percent)
        elif percent >= 100 and grace > today:
            # return quota grace period message
            msg_template_str = f'{qmsg.grace_period_content_prepend} {qmsg.content}\n'
            return_msg += msg_template_str.format(used=rounded_used_val,
                                                  unit=uq.unit,
                                                  allocated=uq.allocated_value,
                                                  zone=uq.zone,
                                                  percent=rounded_percent,
                                                  cut_off_date=grace)
        elif percent >= soft_limit:
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


def get_quota_data(user):
    """
    get user quota data for display on user profile page
    :param user: The User instance
    :return: list of dictionaries, each containing data for a user quota

    Note that percents are in the range 0 to 100
    """
    quota_data = []
    for uq in user.quotas.all():
        allocated = uq.allocated_value
        unit = uq.unit
        uz, dz = uq.get_used_value_by_zone()
        used = uz + dz
        uz = uz * 100.0 / allocated
        dz = dz * 100.0 / allocated
        percent = used * 100.0 / allocated
        remaining = allocated - used
        uq_data = {"used": used,
                   "allocated": allocated,
                   "unit": unit,
                   "uz_percent": uz if uz < 100 else 100,
                   "dz_percent": dz if dz < 100 else 100,
                   "remaining": 0 if remaining < 0 else remaining,
                   "percent_over": 0 if percent < 100 else percent - 100,
                   }
        quota_data.append(uq_data)

    return quota_data


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
