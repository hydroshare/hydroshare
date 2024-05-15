from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.models import User


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
                if len(uqs) > 1:
                    raise ValueError('User has more than one quota')
                for uq in uqs:
                    msg_str = ''
                    if uqs:
                        msg_str = 'Dear ' + uname + ':\n\n'
                        msg = uq.get_quota_message()
                        msg_str += msg

                    if msg_str:
                        msg_str += '\n\nHydroShare Support'
                        subject = 'HydroShare Quota warning'
                        # send email for people monitoring and follow-up as needed
                        send_mail(subject, msg_str, settings.DEFAULT_FROM_EMAIL,
                                  [uemail])
