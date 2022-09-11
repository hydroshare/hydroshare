import os
from datetime import date, timedelta
from uuid import uuid4

from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMultiAlternatives
from django.template import loader
from django.urls import reverse
from django.utils.http import int_to_base36, is_safe_url

from hydroshare import settings as hs_settings


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
    hard_limit = qmsg.hard_limit_percent
    return_msg = ''
    for uq in user.quotas.all():
        percent = uq.used_value * 100.0 / uq.allocated_value
        rounded_percent = round(percent, 2)
        rounded_used_val = round(uq.used_value, 4)

        if percent >= hard_limit or (percent >= 100 and uq.remaining_grace_period == 0):
            # return quota enforcement message
            msg_template_str = '{}{}\n'.format(qmsg.enforce_content_prepend, qmsg.content)
            return_msg += msg_template_str.format(used=rounded_used_val,
                                                  unit=uq.unit,
                                                  allocated=uq.allocated_value,
                                                  zone=uq.zone,
                                                  percent=rounded_percent)
        elif percent >= 100 and uq.remaining_grace_period > 0:
            # return quota grace period message
            cut_off_date = date.today() + timedelta(days=uq.remaining_grace_period)
            msg_template_str = '{}{}\n'.format(qmsg.grace_period_content_prepend, qmsg.content)
            return_msg += msg_template_str.format(used=rounded_used_val,
                                                  unit=uq.unit,
                                                  allocated=uq.allocated_value,
                                                  zone=uq.zone,
                                                  percent=rounded_percent,
                                                  cut_off_date=cut_off_date)
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


def next_url(request):
    """
    Returns URL to redirect to from the ``next`` param in the request.
    """
    next = request.GET.get("next", request.POST.get("next", ""))
    host = request.get_host()
    return next if next and is_safe_url(next, host=host) else None


def subject_template(template, context):
    """
    Loads and renders an email subject template, returning the
    subject string.
    """
    subject = loader.get_template(template).render(context)
    return " ".join(subject.splitlines()).strip()


def send_mail_template(subject, template, addr_from, addr_to, context=None,
                       attachments=None, fail_silently=None, addr_bcc=None,
                       headers=None):
    """
    Send email rendering text and html versions for the specified
    template name using the context dictionary passed in.
    """
    if context is None:
        context = {}
    if attachments is None:
        attachments = []
    if fail_silently is None:
        fail_silently = hs_settings.EMAIL_FAIL_SILENTLY
    # Add template accessible settings from Mezzanine to the context
    # (normally added by a context processor for HTTP requests).
    # context.update(context_settings())
    # Allow for a single address to be passed in.
    # Python 3 strings have an __iter__ method, so the following hack
    # doesn't work: if not hasattr(addr_to, "__iter__"):
    if isinstance(addr_to, str) or isinstance(addr_to, bytes):
        addr_to = [addr_to]
    if addr_bcc is not None and (isinstance(addr_bcc, str) or
                                 isinstance(addr_bcc, bytes)):
        addr_bcc = [addr_bcc]
    # Loads a template passing in vars as context.
    render = lambda type: loader.get_template("%s.%s" % (template, type)).render(context)
    # Create and send email.
    msg = EmailMultiAlternatives(subject, render("txt"),
                                 addr_from, addr_to, addr_bcc,
                                 headers=headers)
    msg.attach_alternative(render("html"), "text/html")
    for attachment in attachments:
        msg.attach(*attachment)
    msg.send(fail_silently=fail_silently)


def send_verification_mail(request, user, verification_type):
    """
    Sends an email with a verification link to users when
    ``ACCOUNTS_VERIFICATION_REQUIRED`` is ```True`` and they're signing
    up, or when they reset a lost password.
    The ``verification_type`` arg is both the name of the urlpattern for
    the verification link, as well as the names of the email templates
    to use.
    """
    verify_url = reverse(verification_type, kwargs={
        "uidb36": int_to_base36(user.id),
        "token": default_token_generator.make_token(user),
    }) + "?next=" + (next_url(request) or "/")
    context = {
        "request": request,
        "user": user,
        "verify_url": verify_url,
    }
    subject_template_name = "email/%s_subject.txt" % verification_type
    subject = subject_template(subject_template_name, context)
    send_mail_template(subject, "email/%s" % verification_type,
                       hs_settings.DEFAULT_FROM_EMAIL, user.email,
                       context=context)


def split_addresses(email_string_list):
    """
    Converts a string containing comma separated email addresses
    into a list of email addresses.
    """
    return [f for f in [s.strip() for s in email_string_list.split(",")] if f]


def admin_url(model, url, object_id=None):
    """
    Returns the URL for the given model and admin url name.
    """
    opts = model._meta
    url = "admin:%s_%s_%s" % (opts.app_label, opts.object_name.lower(), url)
    args = ()
    if object_id is not None:
        args = (object_id,)
    return reverse(url, args=args)


def send_approve_mail(request, user):
    """
    Sends an email to staff in listed in the setting
    ``ACCOUNTS_APPROVAL_EMAILS``, when a new user signs up and the
    ``ACCOUNTS_APPROVAL_REQUIRED`` setting is ``True``.
    """
    approval_emails = split_addresses(hs_settings.ACCOUNTS_APPROVAL_EMAILS)
    if not approval_emails:
        return
    context = {
        "request": request,
        "user": user,
        "change_url": admin_url(user.__class__, "change", user.id),
    }
    subject = subject_template("email/account_approve_subject.txt", context)
    send_mail_template(subject, "email/account_approve",
                       hs_settings.DEFAULT_FROM_EMAIL, approval_emails,
                       context=context)
