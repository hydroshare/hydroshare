from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver

from hs_core.signals import pre_download_file, post_delete_resource, post_create_resource

from .models import Session
from .models import Variable
from .utils import get_client_ip, get_user_type, get_user_email_domain


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

    # set session, user, and ip to None if a request object was not passed as an input kwarg.
    if 'request' not in kwargs.keys():
        session = None
        user = None
        ip = None
    else:
        request = kwargs['request']
        user = request.user
        session = Session.objects.for_request(request, user)
        ip = get_client_ip(request)

    # get the user info
    usertype = get_user_type(session)
    emaildomain = get_user_email_domain(session)

    # format the 'create' kwargs
    msg = Variable.format_kwargs(user_ip=ip,
                                 filename=filename,
                                 resource_size_bytes=resource.size,
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
    
    # set session, user, and ip to None if a request object was not passed as an input kwarg.
    if 'request' not in kwargs.keys():
        session = None
        ip = None
    else:
        request = kwargs['request']
        session = Session.objects.for_request(request, user)
        ip = get_client_ip(request)

    # get the user info
    usertype = get_user_type(session)
    emaildomain = get_user_email_domain(session)

    # format the 'download' kwargs
    msg = Variable.format_kwargs(user_ip=ip,
                                 resource_size_bytes=resource.size,
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
    
    # set session, user, and ip to None if a request object was not passed as an input kwarg.
    if 'request' not in kwargs.keys():
        session = None
        ip = None
    else:
        request = kwargs['request']
        session = Session.objects.for_request(request, user)
        ip = get_client_ip(request)

    # get the user info
    usertype = get_user_type(session)
    emaildomain = get_user_email_domain(session)

    # formate the 'delete' kwargs
    msg = Variable.format_kwargs(user_ip=ip,
                                 resource_type=resource_type,
                                 resource_guid=resource_shortid,
                                 user_type=usertype,
                                 user_email_domain=emaildomain
                                 )

    # record the action
    session.record('delete', value=msg)
