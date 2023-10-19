import json
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver

from hs_core.signals import pre_download_file, pre_download_resource, pre_delete_resource, post_create_resource
from hs_core.enums import RelationTypes
from hs_core.hydroshare.utils import current_site_url

from .models import Session
from .models import Variable
from .utils import get_std_log_fields


@receiver(user_logged_in, dispatch_uid='id_capture_login')
def capture_login(sender, **kwargs):
    session = Session.objects.for_request(kwargs['request'], kwargs['user'])

    # get standard fields
    fields = get_std_log_fields(kwargs['request'], session)

    # format the 'login' kwargs
    msg = Variable.format_kwargs(**fields)

    session.record('login', value=msg)


@receiver(user_logged_out, dispatch_uid='id_capture_logout')
def capture_logout(sender, **kwargs):
    session = Session.objects.for_request(kwargs['request'], kwargs['user'])

    # get standard fields
    fields = get_std_log_fields(kwargs['request'], session)

    # format the 'logout' kwargs
    msg = Variable.format_kwargs(**fields)

    session.record('logout', value=msg)


def get_common_download_fields(**kwargs):
    # get standard fields
    user = None
    if hasattr(kwargs, 'user'):
        user = kwargs['user']
    session = Session.objects.for_request(kwargs['request'], user)
    fields = get_std_log_fields(kwargs['request'], session)

    # add specific fields
    fields['resource_size_bytes'] = kwargs['resource'].size
    fields['resource_type'] = kwargs['resource'].resource_type
    fields['resource_guid'] = kwargs['resource'].short_id

    # MakeDataCount fields
    fields['tracking_visitor_id'] = session.visitor.id
    fields['doi'] = kwargs['resource'].doi
    fields['user_agent'] = kwargs['request'].headers.get('user-agent')

    # MakeDataCount also requires the following metadata about the resource:
    res_metadata = {
        'title': kwargs['resource'].title,
        'creators': " ;".join(str(name) for name in kwargs['resource'].metadata.creators.only('name').all()),
        'is_replaced_by': kwargs['resource'].get_relation_version_res_url(RelationTypes.isReplacedBy) or None,
        'is_version_of': kwargs['resource'].get_relation_version_res_url(RelationTypes.isVersionOf) or None,
        'resource_url': current_site_url() + kwargs['resource'].absolute_url
    }
    if kwargs['resource'].raccess.published:
        res_metadata['publisher'] = str(kwargs['resource'].metadata.publisher),
        res_metadata['publish_date'] = kwargs['resource'].metadata.dates.all().filter(type='published').first()\
            .start_date.strftime("%m/%d/%Y %H:%M:%S.%f")
    fields['resource_metadata'] = json.dumps(res_metadata)
    return fields, session


@receiver(pre_download_file)
def capture_download(**kwargs):

    # exit early if the request is not passed in as a kwarg
    if 'request' not in list(kwargs.keys()):
        return

    # exit early if not human (necessary b/c this action does not require log in)
    is_human = getattr(kwargs['request'], 'is_human', False)
    if not is_human:
        return

    fields, session = get_common_download_fields(**kwargs)
    fields['file_size'] = kwargs['file_size']
    fields['filename'] = kwargs['download_file_name']

    # format the 'download' kwargs
    msg = Variable.format_kwargs(**fields)

    # record the download action
    session.record('download', value=msg,
                   resource=kwargs['resource'],
                   resource_id=kwargs['resource'].short_id)


@receiver(pre_download_resource)
def capture_resource_download(**kwargs):

    # exit early if the request is not passed in as a kwarg
    if 'request' not in list(kwargs.keys()):
        return

    # exit early if not human (necessary b/c this action does not require log in)
    is_human = getattr(kwargs['request'], 'is_human', False)
    if not is_human:
        return

    fields, session = get_common_download_fields(**kwargs)

    # format the 'download' kwargs
    msg = Variable.format_kwargs(**fields)

    # record the download action
    session.record('resource_download', value=msg,
                   resource=kwargs['resource'],
                   resource_id=kwargs['resource'].short_id)


@receiver(post_create_resource)
def capture_resource_create(**kwargs):

    # exit early if the request is not passed in as a kwarg
    if 'request' not in list(kwargs.keys()):
        return

    # get standard fields
    session = Session.objects.for_request(kwargs['request'], kwargs['user'])
    fields = get_std_log_fields(kwargs['request'], session)

    # add specific fields
    fields['resource_size_bytes'] = kwargs['resource'].size
    fields['resource_type'] = kwargs['resource'].resource_type
    fields['resource_guid'] = kwargs['resource'].short_id

    # format the 'create' kwargs
    msg = Variable.format_kwargs(**fields)

    # record the create action
    session.record('create', value=msg, resource=kwargs['resource'],
                   resource_id=kwargs['resource'].short_id)


@receiver(pre_delete_resource)
def capture_resource_delete(**kwargs):

    # exit early if the request object is not passed in as a kwarg
    if 'request' not in list(kwargs.keys()):
        return

    # get standard fields
    session = Session.objects.for_request(kwargs['request'], kwargs['user'])
    fields = get_std_log_fields(kwargs['request'], session)

    # add specific fields
    fields['resource_type'] = kwargs['resource_type']
    fields['resource_guid'] = kwargs['resource_shortkey']

    # format the delete message
    msg = Variable.format_kwargs(**fields)
    resource_id = kwargs['resource_shortkey']

    # record the delete action
    session.record('delete', value=msg, resource_id=resource_id)
