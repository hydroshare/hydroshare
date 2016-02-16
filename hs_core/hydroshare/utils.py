from __future__ import absolute_import

import mimetypes
import os
import json
import tempfile
import logging
import shutil

from django.db.models import get_model, get_models
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils.timezone import now
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import User, Group
from django.core.serializers import get_serializer
from django.core.files import File
from django.core.files.uploadedfile import UploadedFile

from mezzanine.conf import settings

from hs_core.signals import *
from hs_core.models import AbstractResource, ResourceManager, BaseResource, ResourceFile
from hs_core.hydroshare.hs_bagit import create_bag_files
from django_irods.storage import IrodsStorage


logger = logging.getLogger(__name__)


class ResourceFileSizeException(Exception):
    pass


class ResourceFileValidationException(Exception):
    pass


def get_resource_types():
    resource_types = []
    for model in get_models():
        if issubclass(model, AbstractResource) and model != BaseResource:
            if not getattr(model, 'archived_model', False):
                resource_types.append(model)
    return resource_types


def get_resource_instance(app, model_name, pk, or_404=True):
    model = get_model(app, model_name)
    if or_404:
        return get_object_or_404(model, pk=pk)
    else:
        return model.objects.get(pk=pk)


def get_resource_by_shortkey(shortkey, or_404=True):
    try:
        res = BaseResource.objects.get(short_id=shortkey)
    except BaseResource.DoesNotExist:
        if or_404:
            raise Http404(shortkey)
        else:
            raise
    content = res.get_content_model()
    assert content, (res, res.content_model)
    return content


def get_resource_by_doi(doi, or_404=True):
    try:
        res = BaseResource.objects.get(doi=doi)
    except BaseResource.DoesNotExist:
        if or_404:
            raise Http404(doi)
        else:
            raise
    content = res.get_content_model()
    assert content, (res, res.content_model)
    return content


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


# TODO: Tastypie left over. This needs to be deleted
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

# TODO: Tastypie left over. This needs to be deleted
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
        create_bag_files(resource)

    istorage = IrodsStorage()
    # set bag_modified-true AVU pair for the modified resource in iRODS to indicate
    # the resource is modified for on-demand bagging.
    istorage.setAVU(resource.short_id, "bag_modified", "true")


def _validate_email(email):
    from django.core.validators import validate_email
    from django.core.exceptions import ValidationError
    try:
        validate_email(email)
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


def raise_file_size_exception():
    from .resource import FILE_SIZE_LIMIT_FOR_DISPLAY
    error_msg = 'The resource file is larger than the supported size limit: %s.' % FILE_SIZE_LIMIT_FOR_DISPLAY
    raise ResourceFileSizeException(error_msg)


def validate_resource_file_size(resource_files):
    from .resource import check_resource_files
    valid = check_resource_files(resource_files)
    if not valid:
        raise_file_size_exception()


def validate_resource_file_type(resource_cls, files):
    supported_file_types = resource_cls.get_supported_upload_file_types()
    # see if file type checking is needed
    if '.*' in supported_file_types:
        # all file types are supported
        return

    for f in files:
        file_ext = os.path.splitext(f.name)[1]
        if file_ext not in supported_file_types:
            err_msg = "{file_name} is not a supported file type for {res_type} resource"
            err_msg = err_msg.format(file_name=f.name, res_type=resource_cls)
            raise ResourceFileValidationException(err_msg)


def validate_resource_file_count(resource_cls, files, resource=None):
    if len(files) > 0:
        if len(resource_cls.get_supported_upload_file_types()) == 0:
            err_msg = "Content files are not allowed in {res_type} resource".format(res_type=resource_cls)
            raise ResourceFileValidationException(err_msg)

        err_msg = "Multiple content files are not supported in {res_type} resource"
        err_msg = err_msg.format(res_type=resource_cls)
        if len(files) > 1:
            if not resource_cls.can_have_multiple_files():
                raise ResourceFileValidationException(err_msg)

        if resource is not None and resource.files.all().count() > 0:
            if not resource_cls.can_have_multiple_files():
                raise ResourceFileValidationException(err_msg)


def resource_pre_create_actions(resource_type, resource_title, page_redirect_url_key, files=(), metadata=None,
                                **kwargs):
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
        validate_resource_file_count(resource_cls, files)
        validate_resource_file_type(resource_cls, files)

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

    metadata.append({'identifier': {'name': 'hydroShareIdentifier',
                                    'url': '{0}/resource{1}{2}'.format(current_site_url(), '/', resource.short_id)}})

    # remove if there exists the 'type' element as system generates this element
    # remove if there exists 'format' elements - since format elements are system generated based
    # on resource content files
    # remove any 'date' element which is not of type 'valid'. All other date elements are system generated
    for element in list(metadata):
        if 'type' in element or 'format' in element:
            metadata.remove(element)
        if 'date' in element:
            if 'type' in element['date']:
                if element['date']['type'] != 'valid':
                    metadata.remove(element)

    metadata.append({'type': {'url': '{0}/terms/{1}'.format(current_site_url(), resource.__class__.__name__)}})

    metadata.append({'date': {'type': 'created', 'start_date': resource.created}})
    metadata.append({'date': {'type': 'modified', 'start_date': resource.updated}})

    creator_data = get_party_data_from_user(resource.creator)
    metadata.append({'creator': creator_data})


def get_party_data_from_user(user):
    party_data = {}
    user_profile = get_profile(user)
    user_full_name = user.get_full_name()
    if user_full_name:
        party_name = user_full_name
    else:
        party_name = user.username

    party_data['name'] = party_name
    party_data['email'] = user.email
    party_data['description'] = '/user/{uid}/'.format(uid=user.pk)
    party_data['phone'] = user_profile.phone_1
    party_data['organization'] = user_profile.organization
    return party_data


def resource_file_add_pre_process(resource, files, user, extract_metadata=False, **kwargs):
    resource_cls = resource.__class__
    validate_resource_file_size(files)
    validate_resource_file_type(resource_cls, files)
    validate_resource_file_count(resource_cls, files, resource)

    file_validation_dict = {'are_files_valid': True, 'message': 'Files are valid'}
    pre_add_files_to_resource.send(sender=resource_cls, files=files, resource=resource, user=user,
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


def add_file_to_resource(resource, f):
    """
    Add a ResourceFile to a Resource.  Adds the 'format' metadata element to the resource.
    :param resource: Resource to which file should be added
    :param f: File-like object to add to a resource
    :return: The identifier of the ResourceFile added.
    """
    ret = ResourceFile.objects.create(content_object=resource,
                                      resource_file=File(f) if not isinstance(f, UploadedFile) else f)
    # add format metadata element if necessary
    file_format_type = get_file_mime_type(f.name)
    if file_format_type not in [mime.value for mime in resource.metadata.formats.all()]:
        resource.metadata.create_element('format', value=file_format_type)


class ZipContents(object):
    """
    Extract the contents of a zip file one file at a time
    using a generator.
    """
    def __init__(self, zip_file):
        self.zip_file = zip_file

    def black_list_path(self, file_path):
        return file_path.startswith('__MACOSX/')

    def black_list_name(self, file_name):
        return file_name == '.DS_Store'

    def get_files(self):
        temp_dir = tempfile.mkdtemp()
        try:
            file_path = None
            for name_path in self.zip_file.namelist():
                if not self.black_list_path(name_path):
                    name = os.path.basename(name_path)
                    if name != '':
                        if not self.black_list_name(name):
                            self.zip_file.extract(name_path, temp_dir)
                            file_path = os.path.join(temp_dir, name_path)
                            logger.debug("Opening {0} as File with name {1}".format(file_path, name_path))
                            f = File(file=open(file_path, 'rb'),
                                     name=name_path)
                            f.size = os.stat(file_path).st_size
                            yield f
        finally:
            shutil.rmtree(temp_dir)