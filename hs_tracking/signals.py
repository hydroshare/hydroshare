from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver

from .models import Session


@receiver(user_logged_in, dispatch_uid='id_capture_login')
def capture_login(sender, **kwargs):
    session = Session.objects.for_request(kwargs['request'])
    session.record('login')


@receiver(user_logged_out, dispatch_uid='id_capture_logout')
def capture_logout(sender, **kwargs):
    session = Session.objects.for_request(kwargs['request'])
    session.record('logout')
