from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.models import User

from theme.models import UserQuota


class Command(BaseCommand):
    help = "Send users emails for reporting over-quota usages and warnings, etc."

    def add_arguments(self, parser):
        parser.add_argument('--username', nargs='*')

    def handle(self, *args, **options):
        unames = options['username']
        for uname in unames:
            uemail = User.objects.filter(username=uname).first().email
            uqs = UserQuota.objects.filter(user__username=uname).all()
            msg_str = ''
            if uqs:
                msg_str = 'Dear ' + uname + ':\n\n'

            is_first = True
            for uq in uqs:
                if is_first:
                    msg_str += 'Your have used {used}{unit} out of {allocated}{unit} ' \
                               'allocated quota in {zone}'.format(used=uq.used_value,
                                                                  unit=uq.unit,
                                                                  allocated=uq.allocated_value,
                                                                  zone=uq.zone)
                    is_first = False
                else:
                    msg_str += ' and used {used}{unit} out of {allocated}{unit} allocated ' \
                               'quota in {zone}'.format(used=uq.used_value,
                                                        unit=uq.unit,
                                                        allocated=uq.allocated_value,
                                                        zone=uq.zone)
            if msg_str:
                msg_str += '.\n\nHydroShare Support'
                subject = 'Quota warning'
                # send email for people monitoring and follow-up as needed
                send_mail(subject, msg_str, settings.DEFAULT_FROM_EMAIL,
                          [uemail])
