from django.core.mail.backends.smtp import EmailBackend
from django.core.mail.backends.console import EmailBackend as consoleBackend
from django.contrib.sites.models import Site
from django.core.exceptions import ImproperlyConfigured


class BetaEmailBackend(EmailBackend):
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
        with self._lock:
            new_conn_created = self.open()
            if not self.connection or new_conn_created is None:
                # We failed silently on open().
                # Trying to send would be pointless.
                return 0
            num_sent = 0
            for message in email_messages:
                # TODO: are there any other emails that beta HS should actually send?
                if message.subject == "Activate your account in HydroShare":
                    sent = self._send(message)
                    if sent:
                        num_sent += 1
                else:
                    num_sent += consoleBackend.send_messages(message)
            if new_conn_created:
                self.close()
        return num_sent
