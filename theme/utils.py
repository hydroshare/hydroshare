from datetime import date, timedelta

from theme.models import QuotaMessage


def get_quota_message(user):
    """
    get quota warning, grace period, or enforcement message to email users and display
    when the user logins in and display on user profile page
    :param user: The User instance
    :return: quota message string
    """
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
