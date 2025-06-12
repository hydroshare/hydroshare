import os
from uuid import uuid4

from django.db.models import Q

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


def get_quota_message(user):
    """
    get quota warning, grace period, or enforcement message to email users and display
    when the user logins in and display on user profile page
    :param user: The User instance
    :return: quota message string
    """
    from theme.models import QuotaMessage
    if not QuotaMessage.objects.exists():
        QuotaMessage.objects.create()
    qmsg = QuotaMessage.objects.first()
    soft_limit = qmsg.soft_limit_percent
    return_msg = ''
    for uq in user.quotas.all():
        percent = uq.used_value * 100.0 / uq.allocated_value
        rounded_percent = round(percent, 2)
        rounded_used_val = round(uq.used_value, 4)

        if percent >= 100:
            # return quota enforcement message
            msg_template_str = '{}{}\n'.format(qmsg.enforce_content_prepend, qmsg.content)
            return_msg += msg_template_str.format(used=rounded_used_val,
                                                  unit=uq.unit,
                                                  allocated=uq.allocated_value,
                                                  zone=uq.zone,
                                                  percent=rounded_percent)
        elif percent >= soft_limit:
            # return quota warning message
            msg_template_str = '{}{}\n'.format(qmsg.warning_content_prepend, qmsg.content)
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


def get_user_from_username_or_email(username_or_email, **kwargs):
    """
    Get a user object from a username or email address
    :param username_or_email: username or email address
    :return: a user object, or None if no user is found
    """
    from django.contrib.auth import get_user_model
    User = get_user_model()
    try:
        return User.objects.get(
            Q(username__iexact=username_or_email)
            | Q(email__iexact=username_or_email), **kwargs)
    except User.DoesNotExist:
        return None


def get_user_profiles_missing_bucket_name(usernames=None):
    """
    Get all users with UserProfile instances that have missing bucket_name
    :return a tuple of two lists: a list of users and a list of UserProfile instances
    """
    from theme.models import UserProfile
    bad_ups = []
    ups = UserProfile.objects.filter(_bucket_name__isnull=True).filter(user__is_active=True)
    if usernames:
        ups = ups.filter(user__username__in=usernames)
    for up in ups:
        u = up.user
        resources = u.uaccess.owned_resources
        for res in resources:
            # owned is not the same as being the quota_holder
            if res.quota_holder == u:
                bad_ups.append(up)
                break
    return bad_ups
