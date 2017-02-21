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

    # exit early if the request is not passed in as a kwarg
    if 'request' not in kwargs.keys():
        return
    
    # exit early if not human (necessary b/c this action does not require log in)
    is_human = getattr(request, 'is_human', False)
    if not is_human:
        return

    # get input kwargs
    resource = kwargs['resource']
    filename = kwargs['download_file_name']
    request = kwargs['request']

    # get session object for the current user
    user = request.user
    session = Session.objects.for_request(request, user)

    # get user-specific metadata
    ip = get_client_ip(request)
    usertype = get_user_type(session)
    emaildomain = get_user_email_domain(session)

    # format the 'download' kwargs
    msg = Variable.format_kwargs(user_ip=ip,
                                 filename=filename,
                                 resource_size_bytes=resource.size,
                                 resource_type=resource.resource_type,
                                 resource_guid=resource.short_id,
                                 user_type=usertype,
                                 user_email_domain=emaildomain
                                 )

    # record the download action
    session.record('download', value=msg)


@receiver(post_create_resource)
def capture_resource_create(**kwargs):

    # exit early if the request is not passed in as a kwarg
    if 'request' not in kwargs.keys():
        return

    # get user-specific metadata
    resource = kwargs['resource']
    user = kwargs['user']
    request = kwargs['request']

    # get session object for the current user
    session = Session.objects.for_request(request, user)

    # get the user info
    usertype = get_user_type(session)
    emaildomain = get_user_email_domain(session)
    ip = get_client_ip(request)

    # format the 'create' kwargs
    msg = Variable.format_kwargs(user_ip=ip,
                                 resource_size_bytes=resource.size,
                                 resource_type=resource.resource_type,
                                 resource_guid=resource.short_id,
                                 user_type=usertype,
                                 user_email_domain=emaildomain
                                 )

    # record the create action
    session.record('create', value=msg)


@receiver(post_delete_resource)
def capture_resource_delete(**kwargs):

    # exit early if the request object is not passed in as a kwarg
    if 'request' not in kwargs.keys():
        return

    # get input kwargs
    resource_type = kwargs['resource_type']
    resource_shortid = kwargs['resource_shortkey']
    user = kwargs['user']
    request = kwargs['request']

    # get the session object for the current user
    session = Session.objects.for_request(request, user)

    # get user-specific metadata
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

    # record the delete action
    session.record('delete', value=msg)
