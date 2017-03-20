from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.models import User

from theme.models import UserQuota, QuotaMessage


class Command(BaseCommand):
    help = "Send users emails for reporting over-quota usages and warnings, etc."

    def add_arguments(self, parser):
        parser.add_argument('--username', nargs='*')

    def handle(self, *args, **options):
        unames = options['username']
        for uname in unames:
            if User.objects.filter(username=uname).exists():
                user = User.objects.filter(username=uname).first()
                uemail = user.email
                uqs = user.quotas.all()
                msg_str = ''
                if uqs:
                    msg_str = 'Dear ' + uname + ':\n\n'

                for uq in uqs:
                    qmsg = QuotaMessage.objects.first()
                    msg_template_str = '{}{}\n\n'.format(qmsg.warning_content_prepend,
                                                         qmsg.content)
                    msg_str += msg_template_str.format(used=uq.used_value,
                                                       unit=uq.unit,
                                                       allocated=uq.allocated_value,
                                                       zone=uq.zone,
                                                       percent=uq.used_value*100/uq.allocated_value)
                if msg_str:
                    msg_str += '\n\nHydroShare Support'
                    subject = 'Quota warning'
                    # send email for people monitoring and follow-up as needed
                    send_mail(subject, msg_str, settings.DEFAULT_FROM_EMAIL,
                              [uemail])
