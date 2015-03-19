from __future__ import absolute_import

from django.db.models import get_model, get_models
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils.timezone import now
import mimetypes
import os
from hs_core.models import AbstractResource, Bags
from dublincore.models import QualifiedDublinCoreElement
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import User, Group
from django.core.serializers import get_serializer
from mezzanine.conf import settings
from . import hs_bagit
#from hs_scholar_profile.models import *

import importlib
import json
from lxml import etree
import arrow
#from hydroshare import settings

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


def user_from_id(user):
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
                raise Http404('User not found')
            except ObjectDoesNotExist:
                raise Http404('User not found')
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
    resd['dublin_metadata'] = [dc['fields'] for dc in json.loads(js.serialize(res.dublin_metadata.all()))]
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
    resd['dublin_metadata'] = [dc['fields'] for dc in json.loads(js.serialize(res.dublin_metadata.all()))]
    resd['bags'] = [dc['fields'] for dc in json.loads(js.serialize(res.bags.all()))]
    resd['files'] = [dc['fields'] for dc in json.loads(js.serialize(res.files.all()))]
    return json.dumps(resd)


def resource_modified(resource, by_user=None, overwrite_bag=True):
    resource.last_changed_by = by_user
    QualifiedDublinCoreElement.objects.filter(term='DM', object_id=resource.pk).delete()
    QualifiedDublinCoreElement.objects.create(
        term='DM',
        content=now().isoformat(),
        content_object=resource
            )

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

def _get_dc_term_objects(resource_dc_elements, term):
    return [cr_dict for cr_dict in resource_dc_elements if cr_dict['term'] == term]

def _get_user_info(user):
    from hs_core.api import UserResource

    ur = UserResource()
    ur_bundle = ur.build_bundle(obj=user)
    return json.loads(ur.serialize(None, ur.full_dehydrate(ur_bundle), 'application/json'))

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
    port     = getattr(settings, 'MY_SITE_PORT', '')
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
        file_format_type ='application/%s' % os.path.splitext(file_name)[1][1:]

    return file_format_type
