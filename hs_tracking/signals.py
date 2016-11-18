from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver

from hs_core.signals import *

from .models import Session
from .models import Variable
from .utils import *

@receiver(user_logged_in, dispatch_uid='id_capture_login')
def capture_login(sender, **kwargs):
    session = Session.objects.for_request(kwargs['request'], kwargs['user'])
    session.record('login')


@receiver(user_logged_out, dispatch_uid='id_capture_logout')
def capture_logout(sender, **kwargs):
    session = Session.objects.for_request(kwargs['request'], kwargs['user'])
    session.record('logout')

@receiver(pre_download_file)
def capture_download(**kwargs):

    # get input kwargs
    resource = kwargs['resource']
    filename = kwargs['download_file_name']
    request = kwargs['request']
    user = request.user

    # retrieve session
    session = Session.objects.for_request(request, user)

    # calculate total file size
    res_size = resource.get_file_size()

    # get the user info
    usertype = get_user_type(session)
    emaildomain = get_user_email_domain(session)
    ip = get_client_ip(request)

    # format the 'create' kwargs
    msg = Variable.format_kwargs(user_ip=ip,
                                 filename=filename,
                                 resource_size_bytes=res_size,
                                 resource_type=resource.resource_type,
                                 resource_guid=resource.short_id,
                                 user_type=usertype,
                                 user_email_domain=emaildomain
                                 )

    # record the action
    session.record('download', value=msg)

@receiver(post_create_resource)
def capture_resource_create(**kwargs):

    # get input kwargs
    resource = kwargs['resource']
    user = kwargs['user']
    request = kwargs['request']

    # retrieve session
    session = Session.objects.for_request(request, user)

    # calculate total file size
    res_size = resource.get_file_size()

    # get the user info
    usertype = get_user_type(session)
    emaildomain = get_user_email_domain(session)
    ip = get_client_ip(request)

    # format the 'download' kwargs
    msg = Variable.format_kwargs(user_ip=ip,
                                 resource_size_bytes=res_size,
                                 resource_type=resource.resource_type,
                                 resource_guid=resource.short_id,
                                 user_type=usertype,
                                 user_email_domain=emaildomain
                                 )

    # record the action
    session.record('create', value=msg)

@receiver(post_delete_resource)
def capture_resource_delete(**kwargs):

    # get input kwargs
    resource_type = kwargs['resource_type']
    resource_shortid = kwargs['resource_shortkey']
    user = kwargs['user']
    request = kwargs['request']

    # retrieve session
    session = Session.objects.for_request(request, user)

    # get the user info
    usertype = get_user_type(session)
    emaildomain = get_user_email_domain(session)
    ip = get_client_ip(request)

    # formate the 'delete' kwargs
    msg = Variable.format_kwargs(user_ip=ip,
                                 resource_type=resource_type,
                                 resource_guid=resource_shortid,
                                 user_type=usertype,
                                 user_email_domain=emaildomain
                                 )

    # record the action
    session.record('delete', value=msg)

