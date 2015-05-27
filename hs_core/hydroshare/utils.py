from __future__ import absolute_import

import mimetypes
import os
import json

from django.db.models import get_model, get_models
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils.timezone import now
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import User, Group
from django.core.serializers import get_serializer

from mezzanine.conf import settings

from hs_core.signals import *
from hs_core.models import AbstractResource
from . import hs_bagit


class ResourceFileSizeException(Exception):
    pass


class ResourceFileValidationException(Exception):
    pass

cached_resource_types = None

def get_resource_types():
    global cached_resource_types
    #cached_resource_types = filter(lambda x: issubclass(x, AbstractResource), get_models()) if\
    #    not cached_resource_types else cached_resource_types
    cached_resource_types = filter(lambda x: issubclass(x, AbstractResource), get_models())

    return cached_resource_types


def get_resource_instance(app, model_name, pk, or_404=True):
    model = get_model(app, model_name)
    if or_404:
        return get_object_or_404(model, pk=pk)
    else:
        return model.objects.get(pk=pk)


def get_resource_by_shortkey(shortkey, or_404=True):
    models = get_resource_types()
    for model in models:
        m = model.objects.filter(short_id=shortkey)
        if m.exists():
            return m[0]
    if or_404:
        raise Http404(shortkey)
    else:
        raise ObjectDoesNotExist(shortkey)


def get_resource_by_doi(doi, or_404=True):
    models = get_resource_types()
    for model in models:
        m = model.objects.filter(doi=doi)
        if m.exists():
            return m[0]
    if or_404:
        raise Http404(doi)
    else:
        raise ObjectDoesNotExist(doi)


def user_from_id(user, raise404=True):
    if isinstance(user, User):
        return user

    try:
        tgt = User.objects.get(username=user)
    except ObjectDoesNotExist:
        try:
            tgt = User.objects.get(email=user)
        except ObjectDoesNotExist:
            try:
                tgt = User.objects.get(pk=int(user))
            except ValueError:
                if raise404:
                    raise Http404('User not found')
                else:
                    raise User.DoesNotExist
            except ObjectDoesNotExist:
                if raise404:
                    raise Http404('User not found')
                else:
                    raise
    return tgt


def group_from_id(grp):
    if isinstance(grp, Group):
        return grp

    try:
        tgt = Group.objects.get(name=grp)
    except ObjectDoesNotExist:
        try:
            tgt = Group.objects.get(pk=int(grp))
        except TypeError:
            raise Http404('Group not found')
        except ObjectDoesNotExist:
            raise Http404('Group not found')
    return tgt


def serialize_science_metadata(res):
    js = get_serializer('json')()
    resd = json.loads(js.serialize([res]))[0]['fields']
    resd.update(json.loads(js.serialize([res.page_ptr]))[0]['fields'])

    resd['user'] = json.loads(js.serialize([res.user]))[0]['fields']
    resd['resource_uri'] = resd['short_id']
    resd['user']['resource_uri'] = '/u/' + resd['user']['username']
    # TODO: serialize metadata from the res.metadata object
    #resd['dublin_metadata'] = [dc['fields'] for dc in json.loads(js.serialize(res.dublin_metadata.all()))]
    resd['bags'] = [dc['fields'] for dc in json.loads(js.serialize(res.bags.all()))]
    resd['files'] = [dc['fields'] for dc in json.loads(js.serialize(res.files.all()))]
    return json.dumps(resd)


def serialize_system_metadata(res):
    js = get_serializer('json')()
    resd = json.loads(js.serialize([res]))[0]['fields']
    resd.update(json.loads(js.serialize([res.page_ptr]))[0]['fields'])

    resd['user'] = json.loads(js.serialize([res.user]))[0]['fields']
    resd['resource_uri'] = resd['short_id']
    resd['user']['resource_uri'] = '/u/' + resd['user']['username']
    # TODO: serialize metadata from the res.metadata object
    #resd['dublin_metadata'] = [dc['fields'] for dc in json.loads(js.serialize(res.dublin_metadata.all()))]
    resd['bags'] = [dc['fields'] for dc in json.loads(js.serialize(res.bags.all()))]
    resd['files'] = [dc['fields'] for dc in json.loads(js.serialize(res.files.all()))]
    return json.dumps(resd)


def resource_modified(resource, by_user=None, overwrite_bag=True):
    resource.last_changed_by = by_user

    resource.updated = now().isoformat()
    resource.save()
    if resource.metadata.dates.all().filter(type='modified'):
        res_modified_date = resource.metadata.dates.all().filter(type='modified')[0]
        resource.metadata.update_element('date', res_modified_date.id)

    if overwrite_bag:
        for bag in resource.bags.all():
            try:
                bag.bag.delete()
            except:
                pass

            try:
                bag.delete()
            except:
                pass

    hs_bagit.create_bag(resource)


# def _get_user_info(user):
#     from hs_core.api import UserResource
#
#     ur = UserResource()
#     ur_bundle = ur.build_bundle(obj=user)
#     return json.loads(ur.serialize(None, ur.full_dehydrate(ur_bundle), 'application/json'))


def _validate_email( email ):
    from django.core.validators import validate_email
    from django.core.exceptions import ValidationError
    try:
        validate_email( email )
        return True
    except ValidationError:
        return False


def get_profile(user):
    return user.userprofile


def current_site_url():
    """Returns fully qualified URL (no trailing slash) for the current site."""
    from django.contrib.sites.models import Site
    current_site = Site.objects.get_current()
    protocol = getattr(settings, 'MY_SITE_PROTOCOL', 'http')
    port = getattr(settings, 'MY_SITE_PORT', '')
    url = '%s://%s' % (protocol, current_site.domain)
    if port:
        url += ':%s' % port
    return url


def get_file_mime_type(file_name):
    # TODO: looks like the mimetypes module can't find all mime types
    # We may need to user the python magic module instead
    file_format_type = mimetypes.guess_type(file_name)[0]
    if not file_format_type:
        # TODO: this is probably not the right way to get the mime type
        file_format_type = 'application/%s' % os.path.splitext(file_name)[1][1:]

    return file_format_type


def check_file_dict_for_error(file_validation_dict):
    if 'are_files_valid' in file_validation_dict:
        if not file_validation_dict['are_files_valid']:
            error_message = file_validation_dict.get('message', "Uploaded file(s) failed validation.")
            raise ResourceFileValidationException(error_message)


def validate_resource_file_size(resource_files):
    from .resource import check_resource_files, file_size_limit_for_display
    valid = check_resource_files(resource_files)
    if not valid:
        error_msg = 'The resource file is larger than the supported size limit: %s.' % file_size_limit_for_display
        raise ResourceFileSizeException(error_msg)


def resource_pre_create_actions(resource_type, resource_title, page_redirect_url_key, files=(), metadata=None,  **kwargs):
    from.resource import check_resource_type
    if not resource_title:
        resource_title = 'Untitled resource'
    else:
        resource_title = resource_title.strip()
        if len(resource_title) == 0:
            resource_title = 'Untitled resource'

    resource_cls = check_resource_type(resource_type)
    if len(files) > 0:
        validate_resource_file_size(files)

    if not metadata:
        metadata = []
    page_url_dict = {}

    # receivers need to change the values of this dict if file validation fails
    file_validation_dict = {'are_files_valid': True, 'message': 'Files are valid'}

    # Send pre-create resource signal - let any other app populate the empty metadata list object
    # also pass title to other apps, and give other apps a chance to populate page_redirect_url if they want
    # to redirect to their own page for resource creation rather than use core resource creation code
    pre_create_resource.send(sender=resource_cls, metadata=metadata, files=files, title=resource_title,
                             url_key=page_redirect_url_key, page_url_dict=page_url_dict,
                             validate_files=file_validation_dict, **kwargs)

    if len(files) > 0:
        check_file_dict_for_error(file_validation_dict)

    return page_url_dict, resource_title,  metadata


def resource_post_create_actions(resource, user, metadata,  **kwargs):
     # receivers need to change the values of this dict if file validation fails
    file_validation_dict = {'are_files_valid': True, 'message': 'Files are valid'}
    # Send post-create resource signal
    post_create_resource.send(sender=type(resource), resource=resource, user=user,  metadata=metadata,
                              validate_files=file_validation_dict, **kwargs)

    check_file_dict_for_error(file_validation_dict)


def prepare_resource_default_metadata(resource, metadata, res_title):
    add_title = True
    for element in metadata:
        if 'title' in element:
            if 'value' in element['title']:
                res_title = element['title']['value']
                add_title = False
            else:
                metadata.remove(element)
            break

    if add_title:
        metadata.append({'title': {'value': res_title}})

    add_language = True
    for element in metadata:
        if 'language' in element:
            if 'code' in element['language']:
                add_language = False
            else:
                metadata.remove(element)
            break

    if add_language:
        metadata.append({'language': {'code': 'eng'}})

    add_rights = True
    for element in metadata:
        if 'rights' in element:
            if 'statement' in element['rights'] and 'url' in element['rights']:
                add_rights = False
            else:
                metadata.remove(element)
            break

    if add_rights:
        # add the default rights/license element
        metadata.append({'rights':
                             {'statement': 'This resource is shared under the Creative Commons Attribution CC BY.',
                              'url': 'http://creativecommons.org/licenses/by/4.0/'
                             }
                        })

    metadata.append({'identifier': {'name':'hydroShareIdentifier',
                                    'url':'{0}/resource{1}{2}'.format(current_site_url(), '/', resource.short_id)}})

    metadata.append({'date': {'type': 'created', 'start_date': resource.created}})
    metadata.append({'date': {'type': 'modified', 'start_date': resource.updated}})

    if resource.creator.first_name:
        first_creator_name = "{first_name} {last_name}".format(first_name=resource.creator.first_name,
                                                                   last_name=resource.creator.last_name)
    else:
        first_creator_name = resource.creator.username

    first_creator_email = resource.creator.email

    metadata.append({'creator': {'name': first_creator_name, 'email': first_creator_email, 'order': 1}})


def resource_file_add_pre_process(resource, files, user, extract_metadata=False, **kwargs):
    validate_resource_file_size(files)
    file_validation_dict = {'are_files_valid': True, 'message': 'Files are valid'}
    pre_add_files_to_resource.send(sender=resource.__class__, files=files, resource=resource, user=user,
                                   validate_files=file_validation_dict, extract_metadata=extract_metadata, **kwargs)

    check_file_dict_for_error(file_validation_dict)


def resource_file_add_process(resource, files, user, extract_metadata=False, **kwargs):
    from .resource import add_resource_files
    resource_file_objects = add_resource_files(resource.short_id, *files)

    # receivers need to change the values of this dict if file validation fails
    # in case of file validation failure it is assumed the resource type also deleted the file
    file_validation_dict = {'are_files_valid': True, 'message': 'Files are valid'}
    post_add_files_to_resource.send(sender=resource.__class__, files=files, resource=resource, user=user,
                                    validate_files=file_validation_dict, extract_metadata=extract_metadata, **kwargs)

    check_file_dict_for_error(file_validation_dict)

    resource_modified(resource, user)
    return resource_file_objects
