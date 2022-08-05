from smtplib import SMTP
from django.core.mail.backends.smtp import EmailBackend as SmtpBackend
from django.core.mail.backends.console import EmailBackend as ConsoleBackend
from django.contrib.sites.models import Site
from django.core.exceptions import ImproperlyConfigured

from django.template.loader import render_to_string

class BetaEmailBackend(ConsoleBackend):
    def send_messages(self, email_messages):
        """
        Beta Hydroshare specific email backend

        Send one or more EmailMessage objects and return the number of email
        messages sent.
        https://github.com/django/django/blob/main/django/core/mail/backends/smtp.py
        """

        domain = Site.objects.get_current().domain
        if "beta" not in domain:
            raise ImproperlyConfigured(
                "It appears that you are using a Beta specific email backend outside of the beta environment"
            )
        if not email_messages:
            return 0
        num_sent = 0

        for message in email_messages:
            # TODO: are there any other emails that beta HS should actually send?
            activation_subject = render_to_string('email/signup_verify_subject.txt')
            if not message.subject in activation_subject:
                sent = self.write_message(message)
                if sent:
                    num_sent += sent
            else:
                smtp_email_backend = SmtpBackend()
                sent = smtp_email_backend.send_messages(message)
                if sent:
                    num_sent += sent
        return num_sent
