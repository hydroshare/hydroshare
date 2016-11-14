from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver

from .models import Session
from hs_core.signals import pre_download_file


@receiver(user_logged_in, dispatch_uid='id_capture_login')
def capture_login(sender, **kwargs):
    session = Session.objects.for_request(kwargs['request'], kwargs['user'])
    session.record('login')


@receiver(user_logged_out, dispatch_uid='id_capture_logout')
def capture_logout(sender, **kwargs):
    session = Session.objects.for_request(kwargs['request'], kwargs['user'])
    session.record('logout')

@receiver(pre_download_file)
def capture_download(sender, **kwargs):
    session = Session.objects.for_request(kwargs['request'], kwargs['user'])
    resource = kwargs['resource']
    filename = kwargs['download_file_name']
    values = [resource.id, filename, resource.size, resouce.resource_type]
    session.record('download', value=",".join(values))
