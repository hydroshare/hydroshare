from __future__ import absolute_import
import json
import datetime
import pytz
import logging
import os

from django.core.mail import send_mail
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group, User
from django.contrib.sites.models import Site
from django.contrib import messages
from django.contrib.messages import get_messages
from django.utils.decorators import method_decorator
from django.core.exceptions import ValidationError, PermissionDenied, ObjectDoesNotExist
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse, \
    HttpResponseBadRequest, HttpResponseForbidden
from django.shortcuts import get_object_or_404, render_to_response, render, redirect
from django.template import RequestContext
from django.core import signing
from django.db import Error, IntegrityError
from django import forms
from django.views.generic import TemplateView
from django.core.urlresolvers import reverse

from rest_framework import status
from rest_framework.decorators import api_view

from mezzanine.conf import settings
from mezzanine.pages.page_processors import processor_for
from mezzanine.utils.email import subject_template, send_mail_template

import autocomplete_light
from inplaceeditform.commons import get_dict_from_obj, apply_filters
from inplaceeditform.views import _get_http_response, _get_adaptor
from django_irods.icommands import SessionException

from hs_core import hydroshare
from hs_core.hydroshare.utils import get_resource_by_shortkey, resource_modified, resolve_request
from .utils import authorize, upload_from_irods, ACTION_TO_AUTHORIZE, run_script_to_update_hyrax_input_files, \
    get_my_resources_list, send_action_to_take_email, get_coverage_data_dict
from hs_core.models import GenericResource, resource_processor, CoreMetaData, Subject
from hs_core.hydroshare.resource import METADATA_STATUS_SUFFICIENT, METADATA_STATUS_INSUFFICIENT, \
    replicate_resource_bag_to_user_zone

from . import resource_rest_api
from . import resource_metadata_rest_api
from . import user_rest_api
from . import resource_folder_hierarchy

from . import resource_access_api
from . import resource_folder_rest_api
from . import debug_resource_view
from . import resource_ticket_rest_api
from . import apps

from hs_core.hydroshare import utils

from hs_core.signals import *
from hs_access_control.models import PrivilegeCodes, GroupMembershipRequest, GroupResourcePrivilege

from hs_collection_resource.models import CollectionDeletedResource

logger = logging.getLogger(__name__)


def short_url(request, *args, **kwargs):
    try:
        shortkey = kwargs['shortkey']
    except KeyError:
        raise TypeError('shortkey must be specified...')

    m = get_resource_by_shortkey(shortkey)
    return HttpResponseRedirect(m.get_absolute_url())


def verify(request, *args, **kwargs):
    _, pk, email = signing.loads(kwargs['token']).split(':')
    u = User.objects.get(pk=pk)
    if u.email == email:
        if not u.is_active:
            u.is_active=True
            u.save()
            u.groups.add(Group.objects.get(name="Hydroshare Author"))
        from django.contrib.auth import login
        u.backend = settings.AUTHENTICATION_BACKENDS[0]
        login(request, u)
        return HttpResponseRedirect('/account/update/')
    else:
        from django.contrib import messages
        messages.error(request, "Your verification token was invalid.")

    return HttpResponseRedirect('/')


def change_quota_holder(request, shortkey):
    new_holder_uname = request.POST.get('new_holder_username', '')
    if not new_holder_uname:
        return HttpResponseBadRequest()
    new_holder_u = User.objects.filter(username=new_holder_uname).first()
    if not new_holder_u:
        return HttpResponseBadRequest()

    res = utils.get_resource_by_shortkey(shortkey)
    try:
        res.set_quota_holder(request.user, new_holder_u)

        # send notification to the new quota holder
        context = {
            "request": request,
            "user": request.user,
            "new_quota_holder": new_holder_u,
            "resource_uuid": res.short_id,
        }
        subject_template_name = "email/quota_holder_change_subject.txt"
        subject = subject_template(subject_template_name, context)
        send_mail_template(subject, "email/quota_holder_change",
                           settings.DEFAULT_FROM_EMAIL, new_holder_u.email,
                           context=context)
    except PermissionDenied:
        return HttpResponseForbidden()
    except utils.QuotaException as ex:
        msg = 'Failed to change quota holder to {0} since {0} does not have ' \
              'enough quota to hold this new resource. The exception quota message ' \
              'reported for {0} is: '.format(new_holder_u.username) + ex.message
        request.session['validation_error'] = msg

    return HttpResponseRedirect(res.get_absolute_url())


def extract_files_with_paths(request):
    res_files = []
    full_paths = {}
    for key in request.FILES.keys():
        full_path = request.POST.get(key, None)
        f = request.FILES[key]
        res_files.append(f)
        if full_path:
            full_paths[f] = full_path
    return res_files, full_paths


def add_files_to_resource(request, shortkey, *args, **kwargs):
    """
    This view function is called by AJAX in the folder implementation
    :param request: AJAX request
    :param shortkey: resource uuid
    :param args:
    :param kwargs:
    :return: HTTP response with status code indicating success or failure
    """
    resource, _, _ = authorize(request, shortkey,
                               needed_permission=ACTION_TO_AUTHORIZE.EDIT_RESOURCE)
    res_files, full_paths = extract_files_with_paths(request)
    auto_aggregate = request.POST.get("auto_aggregate", 'true').lower() == 'true'
    extract_metadata = request.REQUEST.get('extract-metadata', 'No')
    extract_metadata = True if extract_metadata.lower() == 'yes' else False
    file_folder = request.POST.get('file_folder', None)
    if file_folder is not None:
        if file_folder == "data/contents":
            file_folder = None
        elif file_folder.startswith("data/contents/"):
            file_folder = file_folder[len("data/contents/"):]


    try:
        utils.resource_file_add_pre_process(resource=resource, files=res_files, user=request.user,
                                            extract_metadata=extract_metadata,
                                            folder=file_folder)

    except hydroshare.utils.ResourceFileSizeException as ex:
        msg = 'file_size_error: ' + ex.message
        return HttpResponse(msg, status=500)

    except (hydroshare.utils.ResourceFileValidationException, Exception) as ex:
        msg = 'validation_error: ' + ex.message
        return HttpResponse(msg, status=500)

    try:
        hydroshare.utils.resource_file_add_process(resource=resource, files=res_files,
                                                   user=request.user,
                                                   extract_metadata=extract_metadata,
                                                   folder=file_folder, full_paths=full_paths,
                                                   auto_aggregate=auto_aggregate)

    except (hydroshare.utils.ResourceFileValidationException, Exception) as ex:
        msg = 'validation_error: ' + ex.message
        return HttpResponse(msg, status=500)

    return HttpResponse(status=200)


def _get_resource_sender(element_name, resource):
    core_metadata_element_names = [el_name.lower() for el_name in CoreMetaData.get_supported_element_names()]

    if element_name in core_metadata_element_names:
        sender_resource = GenericResource().__class__
    else:
        sender_resource = resource.__class__

    return sender_resource


def get_supported_file_types_for_resource_type(request, resource_type, *args, **kwargs):
    resource_cls = hydroshare.check_resource_type(resource_type)
    if request.is_ajax:
        # TODO: use try catch
        ajax_response_data = {'file_types': json.dumps(resource_cls.get_supported_upload_file_types())}
        return HttpResponse(json.dumps(ajax_response_data))
    else:
        return HttpResponseRedirect(request.META['HTTP_REFERER'])


def is_multiple_file_upload_allowed(request, resource_type, *args, **kwargs):
    resource_cls = hydroshare.check_resource_type(resource_type)
    if request.is_ajax:
        # TODO: use try catch
        ajax_response_data = {'allow_multiple_file': resource_cls.allow_multiple_file_upload()}
        return HttpResponse(json.dumps(ajax_response_data))
    else:
        return HttpResponseRedirect(request.META['HTTP_REFERER'])


def update_key_value_metadata(request, shortkey, *args, **kwargs):
    """
    This one view function is for CRUD operation for resource key/value arbitrary metadata.
    key/value data in request.POST is assigned to the resource.extra_metadata field
    """
    res, _, _ = authorize(request, shortkey, needed_permission=ACTION_TO_AUTHORIZE.EDIT_RESOURCE)
    post_data = request.POST.copy()
    resource_mode = post_data.pop('resource-mode', None)
    extra_metadata = post_data.dict()
    extra_metadata_copy = extra_metadata.copy()
    for key in extra_metadata_copy:
        if not key:
            extra_metadata.pop(key)

    res.extra_metadata = extra_metadata
    is_update_success = True
    err_message = ""
    try:
        res.save()
    except Error as ex:
        is_update_success = False
        err_message = ex.message

    if is_update_success:
        resource_modified(res, request.user, overwrite_bag=False)
        res_metadata = res.metadata
        res_metadata.set_dirty(True)

    if request.is_ajax():
        if is_update_success:
            ajax_response_data = {'status': 'success',
                                  'is_dirty': res.metadata.is_dirty if
                                  hasattr(res.metadata, 'is_dirty') else False}
        else:
            ajax_response_data = {'status': 'error', 'message': err_message}
        return HttpResponse(json.dumps(ajax_response_data))

    if resource_mode is not None:
        request.session['resource-mode'] = 'edit'

    if is_update_success:
        messages.success(request, "Metadata update successful")
    else:
        messages.error(request, err_message)

    return HttpResponseRedirect(request.META['HTTP_REFERER'])

@api_view(['POST'])
def update_key_value_metadata_public(request, pk):
    res, _, _ = authorize(request, pk, needed_permission=ACTION_TO_AUTHORIZE.EDIT_RESOURCE)

    post_data = request.data.copy()
    res.extra_metadata = post_data

    is_update_success = True

    try:
        res.save()
    except Error as ex:
        is_update_success = False

    if is_update_success:
        resource_modified(res, request.user, overwrite_bag=False)

    if is_update_success:
        return HttpResponse(status=200)
    else:
        return HttpResponse(status=400)


def add_metadata_element(request, shortkey, element_name, *args, **kwargs):
    """This function is normally for adding/creating new resource level metadata elements.
    However, for the metadata element 'subject' (keyword) this function allows for creating,
    updating and deleting metadata elements.
    """
    res, _, _ = authorize(request, shortkey, needed_permission=ACTION_TO_AUTHORIZE.EDIT_RESOURCE)

    is_add_success = False
    err_msg = "Failed to create metadata element '{}'. {}."
    element = None
    sender_resource = _get_resource_sender(element_name, res)
    if element_name.lower() == 'subject' and len(request.POST['value']) == 0:
        # seems the user wants to delete all keywords - no need for pre-check in signal handler
        res.metadata.subjects.all().delete()
        is_add_success = True
        res.update_public_and_discoverable()
        resource_modified(res, request.user, overwrite_bag=False)
    else:
        handler_response = pre_metadata_element_create.send(sender=sender_resource,
                                                            element_name=element_name,
                                                            request=request)
        for receiver, response in handler_response:
            if 'is_valid' in response:
                if response['is_valid']:
                    element_data_dict = response['element_data_dict']
                    if element_name == 'subject':
                        # using set() to remove any duplicate keywords
                        keywords = set([k.strip() for k in element_data_dict['value'].split(',')])
                        keyword_maxlength = Subject._meta.get_field('value').max_length
                        keywords_to_add = []
                        for kw in keywords:
                            if len(kw) > keyword_maxlength:
                                kw = kw[:keyword_maxlength]

                            # skip any duplicate keywords (case insensitive)
                            if kw not in keywords_to_add and kw.lower() not in keywords_to_add:
                                keywords_to_add.append(kw)

                        if len(keywords_to_add) > 0:
                            res.metadata.subjects.all().delete()
                            for kw in keywords_to_add:
                                res.metadata.create_element(element_name, value=kw)
                        is_add_success = True
                    else:
                        try:
                            element = res.metadata.create_element(element_name, **element_data_dict)
                            is_add_success = True
                        except ValidationError as exp:
                            err_msg = err_msg.format(element_name, exp.message)
                            request.session['validation_error'] = err_msg
                        except Error as exp:
                            # some database error occurred
                            err_msg = err_msg.format(element_name, exp.message)
                            request.session['validation_error'] = err_msg
                        except Exception as exp:
                            # some other error occurred
                            err_msg = err_msg.format(element_name, exp.message)
                            request.session['validation_error'] = err_msg

                    if is_add_success:
                        resource_modified(res, request.user, overwrite_bag=False)
                        if res.resource_type == "TimeSeriesResource" and element_name != "subject":
                            res.metadata.is_dirty = True
                            res.metadata.save()
                elif "errors" in response:
                    err_msg = err_msg.format(element_name, response['errors'])

    if request.is_ajax():
        if is_add_success:
            res_public_status = 'public' if res.raccess.public else 'not public'
            res_discoverable_status = 'discoverable' if res.raccess.discoverable \
                else 'not discoverable'
            if res.can_be_public_or_discoverable:
                metadata_status = METADATA_STATUS_SUFFICIENT
            else:
                metadata_status = METADATA_STATUS_INSUFFICIENT

            if element_name == 'subject':
                ajax_response_data = {'status': 'success', 'element_name': element_name,
                                      'metadata_status': metadata_status,
                                      'res_public_status': res_public_status,
                                      'res_discoverable_status': res_discoverable_status}
            elif element_name.lower() == 'site' and res.resource_type == 'TimeSeriesResource':
                # get the spatial coverage element
                spatial_coverage_dict = get_coverage_data_dict(res)
                ajax_response_data = {'status': 'success',
                                      'element_name': element_name,
                                      'spatial_coverage': spatial_coverage_dict,
                                      'metadata_status': metadata_status,
                                      'res_public_status': res_public_status,
                                      'res_discoverable_status': res_discoverable_status
                                      }
                if element is not None:
                    ajax_response_data['element_id'] = element.id
            else:
                ajax_response_data = {'status': 'success',
                                      'element_name': element_name,
                                      'metadata_status': metadata_status,
                                      'res_public_status': res_public_status,
                                      'res_discoverable_status': res_discoverable_status
                                      }
                if element is not None:
                    ajax_response_data['element_id'] = element.id

            ajax_response_data['is_dirty'] = res.metadata.is_dirty if \
                hasattr(res.metadata, 'is_dirty') else False

            return JsonResponse(ajax_response_data)
        else:
            ajax_response_data = {'status': 'error', 'message': err_msg}
            return JsonResponse(ajax_response_data)

    if 'resource-mode' in request.POST:
        request.session['resource-mode'] = 'edit'

    return HttpResponseRedirect(request.META['HTTP_REFERER'])


def update_metadata_element(request, shortkey, element_name, element_id, *args, **kwargs):
    res, _, _ = authorize(request, shortkey, needed_permission=ACTION_TO_AUTHORIZE.EDIT_RESOURCE)
    sender_resource = _get_resource_sender(element_name, res)
    handler_response = pre_metadata_element_update.send(sender=sender_resource,
                                                        element_name=element_name,
                                                        element_id=element_id, request=request)
    is_update_success = False
    err_msg = "Failed to update metadata element '{}'. {}."
    for receiver, response in handler_response:
        if 'is_valid' in response:
            if response['is_valid']:
                element_data_dict = response['element_data_dict']
                try:
                    res.metadata.update_element(element_name, element_id, **element_data_dict)
                    post_handler_response = post_metadata_element_update.send(
                        sender=sender_resource, element_name=element_name, element_id=element_id)
                    is_update_success = True
                    # this is how we handle if a post_metadata_element_update receiver
                    # is not implemented in the resource type's receivers.py
                    element_exists = True
                    for receiver, response in post_handler_response:
                        if 'element_exists' in response:
                            element_exists = response['element_exists']

                except ValidationError as exp:
                    err_msg = err_msg.format(element_name, exp.message)
                    request.session['validation_error'] = err_msg
                except Error as exp:
                    # some database error occurred
                    err_msg = err_msg.format(element_name, exp.message)
                    request.session['validation_error'] = err_msg
                # TODO: it's brittle to embed validation logic at this level.
                if element_name == 'title':
                    res.update_public_and_discoverable()
                if is_update_success:
                    resource_modified(res, request.user, overwrite_bag=False)
                    if res.resource_type == "TimeSeriesResource" and element_name != "subject":
                        res.metadata.is_dirty = True
                        res.metadata.save()
            elif "errors" in response:
                err_msg = err_msg.format(element_name, response['errors'])

    if request.is_ajax():
        if is_update_success:
            res_public_status = 'public' if res.raccess.public else 'not public'
            res_discoverable_status = 'discoverable' if res.raccess.discoverable \
                else 'not discoverable'
            if res.can_be_public_or_discoverable:
                metadata_status = METADATA_STATUS_SUFFICIENT
            else:
                metadata_status = METADATA_STATUS_INSUFFICIENT
            if element_name.lower() == 'site' and (res.resource_type == 'TimeSeriesResource' or
                                                   res.resource_type == 'CompositeResource'):
                # get the spatial coverage element
                spatial_coverage_dict = get_coverage_data_dict(res)
                ajax_response_data = {'status': 'success',
                                      'element_name': element_name,
                                      'spatial_coverage': spatial_coverage_dict,
                                      'metadata_status': metadata_status,
                                      'res_public_status': res_public_status,
                                      'res_discoverable_status': res_discoverable_status,
                                      'element_exists': element_exists}
            else:
                ajax_response_data = {'status': 'success',
                                      'element_name': element_name,
                                      'metadata_status': metadata_status,
                                      'res_public_status': res_public_status,
                                      'res_discoverable_status': res_discoverable_status,
                                      'element_exists': element_exists}

            ajax_response_data['is_dirty'] = res.metadata.is_dirty if \
                hasattr(res.metadata, 'is_dirty') else False

            return JsonResponse(ajax_response_data)
        else:
            ajax_response_data = {'status': 'error', 'message': err_msg}
            return JsonResponse(ajax_response_data)

    if 'resource-mode' in request.POST:
        request.session['resource-mode'] = 'edit'

    return HttpResponseRedirect(request.META['HTTP_REFERER'])


@api_view(['GET'])
def file_download_url_mapper(request, shortkey):
    """ maps the file URIs in resourcemap document to django_irods download view function"""
    try:
        res, _, _ = authorize(request, shortkey,
                              needed_permission=ACTION_TO_AUTHORIZE.VIEW_RESOURCE,
                              raises_exception=False)
    except ObjectDoesNotExist:
        return HttpResponse("resource not found", status=status.HTTP_404_NOT_FOUND)
    except PermissionDenied:
        return HttpResponse("access not authorized", status=status.HTTP_401_UNAUTHORIZED)

    if __debug__:
        logger.debug("request path is {}".format(request.path))
    path_split = request.path.split('/')[2:]  # strip /resource/
    public_file_path = '/'.join(path_split)
    # logger.debug("public_file_path is {}".format(public_file_path))
    istorage = res.get_irods_storage()
    if request.GET.get('zipped', "False") == "True":
        file_download_url = istorage.url(public_file_path) + "?zipped=True"
    else:
        file_download_url = istorage.url(public_file_path)
    if __debug__:
        logger.debug("redirect is {}".format(file_download_url))
    return HttpResponseRedirect(file_download_url)


def delete_metadata_element(request, shortkey, element_name, element_id, *args, **kwargs):
    res, _, _ = authorize(request, shortkey, needed_permission=ACTION_TO_AUTHORIZE.EDIT_RESOURCE)
    res.metadata.delete_element(element_name, element_id)
    res.update_public_and_discoverable()
    resource_modified(res, request.user, overwrite_bag=False)
    request.session['resource-mode'] = 'edit'
    return HttpResponseRedirect(request.META['HTTP_REFERER'])


def delete_file(request, shortkey, f, *args, **kwargs):
    res, _, user = authorize(request, shortkey, needed_permission=ACTION_TO_AUTHORIZE.EDIT_RESOURCE)
    hydroshare.delete_resource_file(shortkey, f, user)  # calls resource_modified
    request.session['resource-mode'] = 'edit'
    return HttpResponseRedirect(request.META['HTTP_REFERER'])


def delete_multiple_files(request, shortkey, *args, **kwargs):
    res, _, user = authorize(request, shortkey, needed_permission=ACTION_TO_AUTHORIZE.EDIT_RESOURCE)
    # file_ids is a string of file ids separated by comma
    f_ids = request.POST['file_ids']
    f_id_list = f_ids.split(',')
    for f_id in f_id_list:
        f_id = f_id.strip()
        try:
            hydroshare.delete_resource_file(shortkey, f_id, user)  # calls resource_modified
        except ObjectDoesNotExist as ex:
            # Since some specific resource types such as feature resource type delete all other
            # dependent content files together when one file is deleted, we make this specific
            # ObjectDoesNotExist exception as legitimate in delete_multiple_files() without
            # raising this specific exception
            logger.warn(ex.message)
            continue
    request.session['resource-mode'] = 'edit'
    return HttpResponseRedirect(request.META['HTTP_REFERER'])


def delete_resource(request, shortkey, *args, **kwargs):
    res, _, user = authorize(request, shortkey, needed_permission=ACTION_TO_AUTHORIZE.DELETE_RESOURCE)

    res_title = res.metadata.title
    res_id = shortkey
    res_type = res.resource_type
    resource_related_collections = [col for col in res.collections.all()]
    owners_list = [owner for owner in res.raccess.owners.all()]
    ajax_response_data = {'status': 'success'}
    try:
        hydroshare.delete_resource(shortkey)
    except ValidationError as ex:
        if request.is_ajax():
            ajax_response_data['status'] = 'error'
            ajax_response_data['message'] = ex.message
            return JsonResponse(ajax_response_data)
        else:
            request.session['validation_error'] = ex.message
            return HttpResponseRedirect(request.META['HTTP_REFERER'])

    # if the deleted resource is part of any collection resource, then for each of those collection
    # create a CollectionDeletedResource object which can then be used to list collection deleted
    # resources on collection resource landing page
    for collection_res in resource_related_collections:
        o=CollectionDeletedResource.objects.create(
             resource_title=res_title,
             deleted_by=user,
             resource_id=res_id,
             resource_type=res_type,
             collection=collection_res
             )
        o.resource_owners.add(*owners_list)

    post_delete_resource.send(sender=type(res), request=request, user=user,
                              resource_shortkey=shortkey, resource=res,
                              resource_title=res_title, resource_type=res_type, **kwargs)

    if request.is_ajax():
        return JsonResponse(ajax_response_data)
    else:
        return HttpResponseRedirect('/my-resources/')


def rep_res_bag_to_irods_user_zone(request, shortkey, *args, **kwargs):
    '''
    This function needs to be called via AJAX. The function replicates resource bag to iRODS user zone on users.hydroshare.org
    which is federated with hydroshare zone under the iRODS user account corresponding to a HydroShare user. This function
    should only be called or exposed to be called from web interface when a corresponding iRODS user account on hydroshare
    user Zone exists. The purpose of this function is to allow HydroShare resource bag that a HydroShare user has access
    to be copied to HydroShare user's iRODS space in HydroShare user zone so that users can do analysis or computations on
    the resource
    Args:
        request: an AJAX request
        shortkey: UUID of the resource to be copied to the login user's iRODS user space

    Returns:
        JSON list that indicates status of resource replication, i.e., success or error
    '''
    res, authorized, user = authorize(request, shortkey, needed_permission=ACTION_TO_AUTHORIZE.VIEW_RESOURCE, raises_exception=False)
    if not authorized:
        return HttpResponse(
        json.dumps({"error": "You are not authorized to replicate this resource."}),
        content_type="application/json"
        )

    try:
        replicate_resource_bag_to_user_zone(user, shortkey)
        return HttpResponse(
            json.dumps({"success": "This resource bag zip file has been successfully copied to your iRODS user zone."}),
            content_type = "application/json"
        )
    except SessionException as ex:
        return HttpResponse(
        json.dumps({"error": ex.stderr}),
        content_type="application/json"
        )
    except utils.QuotaException as ex:
        return HttpResponse(
            json.dumps({"error": ex.message}),
            content_type="application/json"
        )
    except ValidationError as ex:
        return HttpResponse(
            json.dumps({"error": ex.message}),
            content_type="application/json"
        )


def copy_resource(request, shortkey, *args, **kwargs):
    res, authorized, user = authorize(request, shortkey,
                                      needed_permission=ACTION_TO_AUTHORIZE.VIEW_RESOURCE)
    new_resource = None
    try:
        new_resource = hydroshare.create_empty_resource(shortkey, user, action='copy')
        new_resource = hydroshare.copy_resource(res, new_resource, user=request.user)
    except Exception as ex:
        if new_resource:
            new_resource.delete()
        request.session['resource_creation_error'] = 'Failed to copy this resource: ' + ex.message
        return HttpResponseRedirect(res.get_absolute_url())

    # go to resource landing page
    request.session['just_created'] = True
    request.session['just_copied'] = True
    return HttpResponseRedirect(new_resource.get_absolute_url())


@api_view(['POST'])
def copy_resource_public(request, pk):
    response = copy_resource(request, pk)
    return HttpResponse(response.url.split('/')[2], status=202)


def create_new_version_resource(request, shortkey, *args, **kwargs):
    res, authorized, user = authorize(request, shortkey,
                                      needed_permission=ACTION_TO_AUTHORIZE.CREATE_RESOURCE_VERSION)

    if res.locked_time:
        elapsed_time = datetime.datetime.now(pytz.utc) - res.locked_time
        if elapsed_time.days >= 0 or elapsed_time.seconds > settings.RESOURCE_LOCK_TIMEOUT_SECONDS:
            # clear the lock since the elapsed time is greater than timeout threshold
            res.locked_time = None
            res.save()
        else:
            # cannot create new version for this resource since the resource is locked by another
            # user
            request.session['resource_creation_error'] = 'Failed to create a new version for ' \
                                                         'this resource since another user is ' \
                                                         'creating a new version for this ' \
                                                         'resource synchronously.'
            return HttpResponseRedirect(res.get_absolute_url())

    new_resource = None
    try:
        # lock the resource to prevent concurrent new version creation since only one new version for an
        # obsoleted resource is allowed
        res.locked_time = datetime.datetime.now(pytz.utc)
        res.save()
        new_resource = hydroshare.create_empty_resource(shortkey, user)
        new_resource = hydroshare.create_new_version_resource(res, new_resource, user)
    except Exception as ex:
        if new_resource:
            new_resource.delete()
        # release the lock if new version of the resource failed to create
        res.locked_time = None
        res.save()
        request.session['resource_creation_error'] = 'Failed to create a new version of ' \
                                                     'this resource: ' + ex.message
        return HttpResponseRedirect(res.get_absolute_url())

    # release the lock if new version of the resource is created successfully
    res.locked_time = None
    res.save()

    # go to resource landing page
    request.session['just_created'] = True
    return HttpResponseRedirect(new_resource.get_absolute_url())


@api_view(['POST'])
def create_new_version_resource_public(request, pk):
    redirect = create_new_version_resource(request, pk)
    return HttpResponse(redirect.url.split('/')[2], status=202)


def publish(request, shortkey, *args, **kwargs):
    # only resource owners are allowed to change resource flags (e.g published)
    res, _, _ = authorize(request, shortkey, needed_permission=ACTION_TO_AUTHORIZE.SET_RESOURCE_FLAG)

    try:
        hydroshare.publish_resource(request.user, shortkey)
    except ValidationError as exp:
        request.session['validation_error'] = exp.message
    else:
        request.session['just_published'] = True
    return HttpResponseRedirect(request.META['HTTP_REFERER'])


def set_resource_flag(request, shortkey, *args, **kwargs):
    # only resource owners are allowed to change resource flags
    res, _, user = authorize(request, shortkey, needed_permission=ACTION_TO_AUTHORIZE.SET_RESOURCE_FLAG)
    flag = resolve_request(request).get('flag', None)
    if flag == 'make_public':
        _set_resource_sharing_status(request, user, res, flag_to_set='public', flag_value=True)
    elif flag == 'make_private' or flag == 'make_not_discoverable':
        _set_resource_sharing_status(request, user, res, flag_to_set='discoverable', flag_value=False)
    elif flag == 'make_discoverable':
        _set_resource_sharing_status(request, user, res, flag_to_set='discoverable', flag_value=True)
    elif flag == 'make_not_shareable':
        _set_resource_sharing_status(request, user, res, flag_to_set='shareable', flag_value=False)
    elif flag == 'make_shareable':
       _set_resource_sharing_status(request, user, res, flag_to_set='shareable', flag_value=True)
    elif flag == 'make_require_lic_agreement':
        res.set_require_download_agreement(user, value=True)
    elif flag == 'make_not_require_lic_agreement':
        res.set_require_download_agreement(user, value=False)

    if request.META.get('HTTP_REFERER', None):
        request.session['resource-mode'] = request.POST.get('resource-mode', 'view')
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', None))

    return HttpResponse(status=202)


@api_view(['POST'])
def set_resource_flag_public(request, pk):
    http_request = request._request
    http_request.data = request.data.copy()
    response = set_resource_flag(http_request, pk)

    messages = get_messages(request)
    for message in messages:
        if(message.tags == "error"):
            return HttpResponse(message, status=400)
    return response

def share_resource_with_user(request, shortkey, privilege, user_id, *args, **kwargs):
    """this view function is expected to be called by ajax"""
    return _share_resource(request, shortkey, privilege, user_id, user_or_group='user')


def share_resource_with_group(request, shortkey, privilege, group_id, *args, **kwargs):
    """this view function is expected to be called by ajax"""
    return _share_resource(request, shortkey, privilege, group_id, user_or_group='group')


def _share_resource(request, shortkey, privilege, user_or_group_id, user_or_group):
    """
    share resource with a user or group
    :param request:
    :param shortkey: id of the resource to share with
    :param privilege: access privilege need for the resource
    :param user_or_group_id: id of the user or group with whom the resource to be shared
    :param user_or_group: indicates if the resource to be shared with a user or group. A value of 'user' will share
                          the resource with a user whose id is provided with the parameter 'user_or_group_id'.
                          Any other value for this parameter assumes resource to be shared with a group.
    :return:
    """

    res, _, user = authorize(request, shortkey, needed_permission=ACTION_TO_AUTHORIZE.VIEW_RESOURCE)
    user_to_share_with = None
    group_to_share_with = None
    status_code = 200
    if user_or_group == 'user':
        user_to_share_with = utils.user_from_id(user_or_group_id)
    else:
        group_to_share_with = utils.group_from_id(user_or_group_id)

    status = 'success'
    err_message = ''
    if privilege == 'view':
        access_privilege = PrivilegeCodes.VIEW
    elif privilege == 'edit':
        access_privilege = PrivilegeCodes.CHANGE
    elif privilege == 'owner':
        if user_or_group != 'user':
            status_code = 400
            err_message = "Group can't have owner privilege over a resource"
            access_privilege = PrivilegeCodes.NONE
        else:
            access_privilege = PrivilegeCodes.OWNER
    else:
        status_code = 400
        err_message = "Not a valid privilege"
        access_privilege = PrivilegeCodes.NONE

    if access_privilege != PrivilegeCodes.NONE:
        try:
            if user_or_group == 'user':
                user.uaccess.share_resource_with_user(res, user_to_share_with, access_privilege)
            else:
                user.uaccess.share_resource_with_group(res, group_to_share_with, access_privilege)
        except PermissionDenied as exp:
            status = 'error'
            err_message = exp.message
    else:
        status = 'error'

    current_user_privilege = res.raccess.get_effective_privilege(user)
    if current_user_privilege == PrivilegeCodes.VIEW:
        current_user_privilege = "view"
    elif current_user_privilege == PrivilegeCodes.CHANGE:
        current_user_privilege = "change"
    elif current_user_privilege == PrivilegeCodes.OWNER:
        current_user_privilege = "owner"

    if user_or_group == 'user':
        is_current_user = False
        if user == user_to_share_with:
            is_current_user = True

        picture_url = 'No picture provided'
        if user_to_share_with.userprofile.picture:
            picture_url = user_to_share_with.userprofile.picture.url

        ajax_response_data = {'status': status, 'name': user_to_share_with.get_full_name(),
                              'username': user_to_share_with.username, 'privilege_granted': privilege,
                              'current_user_privilege': current_user_privilege,
                              'profile_pic': picture_url, 'is_current_user': is_current_user,
                              'error_msg': err_message}

    else:
        group_pic_url = 'No picture provided'
        if group_to_share_with.gaccess.picture:
            group_pic_url = group_to_share_with.gaccess.picture.url

        ajax_response_data = {'status': status, 'name': group_to_share_with.name,
                              'privilege_granted': privilege, 'group_pic': group_pic_url,
                              'current_user_privilege': current_user_privilege,
                              'error_msg': err_message}

    return HttpResponse(json.dumps(ajax_response_data), status=status_code)


def unshare_resource_with_user(request, shortkey, user_id, *args, **kwargs):
    """this view function is expected to be called by ajax"""

    res, _, user = authorize(request, shortkey, needed_permission=ACTION_TO_AUTHORIZE.VIEW_RESOURCE)
    user_to_unshare_with = utils.user_from_id(user_id)
    ajax_response_data = {'status': 'success'}
    try:
        user.uaccess.unshare_resource_with_user(res, user_to_unshare_with)
        if user not in res.raccess.view_users:
            # user has no explict access to the resource - redirect to resource listing page
            ajax_response_data['redirect_to'] = '/my-resources/'

    except PermissionDenied as exp:
        ajax_response_data['status'] = 'error'
        ajax_response_data['message'] = exp.message

    return JsonResponse(ajax_response_data)


def unshare_resource_with_group(request, shortkey, group_id, *args, **kwargs):
    """this view function is expected to be called by ajax"""

    res, _, user = authorize(request, shortkey, needed_permission=ACTION_TO_AUTHORIZE.VIEW_RESOURCE)
    group_to_unshare_with = utils.group_from_id(group_id)
    ajax_response_data = {'status': 'success'}
    try:
        user.uaccess.unshare_resource_with_group(res, group_to_unshare_with)
        if user not in res.raccess.view_users:
            # user has no explicit access to the resource - redirect to resource listing page
            ajax_response_data['redirect_to'] = '/my-resources/'
    except PermissionDenied as exp:
        ajax_response_data['status'] = 'error'
        ajax_response_data['message'] = exp.message

    return JsonResponse(ajax_response_data)


def undo_share_resource_with_user(request, shortkey, user_id, *args, **kwargs):
    """this view function is expected to be called by ajax"""

    res, _, user = authorize(request, shortkey, needed_permission=ACTION_TO_AUTHORIZE.VIEW_RESOURCE)
    user_to_unshare_with = utils.user_from_id(user_id)
    ajax_response_data = {'status': 'success'}
    try:
        user.uaccess.undo_share_resource_with_user(res, user_to_unshare_with)
        undo_user_privilege = res.raccess.get_effective_privilege(user_to_unshare_with)
        if undo_user_privilege == PrivilegeCodes.VIEW:
            undo_user_privilege = "view"
        elif undo_user_privilege == PrivilegeCodes.CHANGE:
            undo_user_privilege = "change"
        elif undo_user_privilege == PrivilegeCodes.OWNER:
            undo_user_privilege = "owner"
        else:
            undo_user_privilege = 'none'
        ajax_response_data['undo_user_privilege'] = undo_user_privilege

        if user not in res.raccess.view_users:
            # user has no explict access to the resource - redirect to resource listing page
            ajax_response_data['redirect_to'] = '/my-resources/'

    except PermissionDenied as exp:
        ajax_response_data['status'] = 'error'
        ajax_response_data['message'] = exp.message

    return JsonResponse(ajax_response_data)


def undo_share_resource_with_group(request, shortkey, group_id, *args, **kwargs):
    """this view function is expected to be called by ajax"""

    res, _, user = authorize(request, shortkey, needed_permission=ACTION_TO_AUTHORIZE.VIEW_RESOURCE)
    group_to_unshare_with = utils.group_from_id(group_id)
    ajax_response_data = {'status': 'success'}
    try:
        user.uaccess.undo_share_resource_with_group(res, group_to_unshare_with)
        if group_to_unshare_with in res.raccess.edit_groups:
            undo_group_privilege = 'change'
        elif group_to_unshare_with in res.raccess.view_groups:
            undo_group_privilege = 'view'
        else:
            undo_group_privilege = 'none'
        ajax_response_data['undo_group_privilege'] = undo_group_privilege

        if user not in res.raccess.view_users:
            # user has no explicit access to the resource - redirect to resource listing page
            ajax_response_data['redirect_to'] = '/my-resources/'
    except PermissionDenied as exp:
        ajax_response_data['status'] = 'error'
        ajax_response_data['message'] = exp.message

    return JsonResponse(ajax_response_data)


# view functions mapped with INPLACE_SAVE_URL(/hsapi/save_inline/) for Django inplace editing
def save_ajax(request):
    if not request.method == 'POST':
        return _get_http_response({'errors': 'It is not a POST request'})
    adaptor = _get_adaptor(request, 'POST')
    if not adaptor:
        return _get_http_response({'errors': 'Params insufficient'})
    if not adaptor.can_edit():
        return _get_http_response({'errors': 'You can not edit this content'})
    value = adaptor.loads_to_post(request)
    new_data = get_dict_from_obj(adaptor.obj)
    form_class = adaptor.get_form_class()
    field_name = adaptor.field_name
    new_data['in_menus'] = ''
    form = form_class(data=new_data, instance=adaptor.obj)
    try:
        value_edit = adaptor.get_value_editor(value)
        value_edit_with_filter = apply_filters(value_edit, adaptor.filters_to_edit)
        new_data[field_name] = value_edit_with_filter
        new_data[field_name] = value_edit_with_filter
        if form.is_valid():
            adaptor.save(value_edit_with_filter)
            return _get_http_response({'errors': False,
                                        'value': adaptor.render_value_edit()})
        messages = [] # The error is for another field that you are editing
        for field_name_error, errors_field in form.errors.items():
            for error in errors_field:
                messages.append("%s: %s" % (field_name_error, unicode(error)))
        message_i18n = ','.join(messages)
        return _get_http_response({'errors': message_i18n})
    except ValidationError as error: # The error is for a field that you are editing
        message_i18n = ', '.join([u"%s" % m for m in error.messages])
        return _get_http_response({'errors': message_i18n})


def verify_account(request, *args, **kwargs):
    context = {
            'username' : request.GET['username'],
            'email' : request.GET['email']
        }
    return render_to_response('pages/verify-account.html', context, context_instance=RequestContext(request))


@processor_for('resend-verification-email')
def resend_verification_email(request):
    u = get_object_or_404(User, username=request.GET['username'], email=request.GET['email'])
    try:
        token = signing.dumps('verify_user_email:{0}:{1}'.format(u.pk, u.email))
        u.email_user(
            'Please verify your new Hydroshare account.',
            """
This is an automated email from Hydroshare.org. If you requested a Hydroshare account, please
go to http://{domain}/verify/{token}/ and verify your account.
""".format(
            domain=Site.objects.get_current().domain,
            token=token
        ))

        context = {
            'is_email_sent' : True
        }
        return render_to_response('pages/verify-account.html', context, context_instance=RequestContext(request))
    except:
        pass # FIXME should log this instead of ignoring it.


class FilterForm(forms.Form):
    start = forms.IntegerField(required=False)
    published = forms.BooleanField(required=False)
    edit_permission = forms.BooleanField(required=False)
    owner = forms.CharField(required=False)
    user = forms.ModelChoiceField(queryset=User.objects.all(), required=False)
    from_date = forms.DateTimeField(required=False)


class GroupForm(forms.Form):
    name = forms.CharField(required=True)
    description = forms.CharField(required=True)
    purpose = forms.CharField(required=False)
    picture = forms.ImageField(required=False)
    privacy_level = forms.CharField(required=True)
    auto_approve = forms.BooleanField(required=False)

    def clean_privacy_level(self):
        data = self.cleaned_data['privacy_level']
        if data not in ('public', 'private', 'discoverable'):
            raise forms.ValidationError("Invalid group privacy level.")
        return data

    def _set_privacy_level(self, group, privacy_level):
        if privacy_level == 'public':
            group.gaccess.public = True
            group.gaccess.discoverable = True
        elif privacy_level == 'private':
            group.gaccess.public = False
            group.gaccess.discoverable = False
        elif privacy_level == 'discoverable':
            group.gaccess.discoverable = True
            group.gaccess.public = False

        group.gaccess.save()


class GroupCreateForm(GroupForm):
    def save(self, request):
        frm_data = self.cleaned_data

        new_group = request.user.uaccess.create_group(title=frm_data['name'],
                                                      description=frm_data['description'],
                                                      purpose=frm_data['purpose'],
                                                      auto_approve=frm_data['auto_approve'])
        if 'picture' in request.FILES:
            new_group.gaccess.picture = request.FILES['picture']

        privacy_level = frm_data['privacy_level']
        self._set_privacy_level(new_group, privacy_level)
        return new_group


class GroupUpdateForm(GroupForm):

    def update(self, group_to_update, request):
        frm_data = self.cleaned_data
        group_to_update.name = frm_data['name']
        group_to_update.save()
        group_to_update.gaccess.description = frm_data['description']
        group_to_update.gaccess.purpose = frm_data['purpose']
        group_to_update.gaccess.auto_approve = frm_data['auto_approve']
        if 'picture' in request.FILES:
            group_to_update.gaccess.picture = request.FILES['picture']

        privacy_level = frm_data['privacy_level']
        self._set_privacy_level(group_to_update, privacy_level)

@processor_for('my-resources')
@login_required
def my_resources(request, page):

    resource_collection = get_my_resources_list(request)
    context = {'collection': resource_collection}

    return context


@processor_for(GenericResource)
def add_generic_context(request, page):
    user = request.user
    user_zone_account_exist = utils.get_user_zone_status_info(user)

    class AddUserForm(forms.Form):
        user = forms.ModelChoiceField(User.objects.filter(is_active=True).all(),
                                      widget=autocomplete_light.ChoiceWidget("UserAutocomplete"))

    class AddGroupForm(forms.Form):
        group = forms.ModelChoiceField(Group.objects.filter(gaccess__active=True).exclude(name='Hydroshare Author').all(),
                                       widget=autocomplete_light.ChoiceWidget("GroupAutocomplete"))

    return {
        'add_owner_user_form': AddUserForm(),
        'add_view_user_form': AddUserForm(),
        'add_edit_user_form': AddUserForm(),
        'add_view_group_form': AddGroupForm(),
        'add_edit_group_form': AddGroupForm(),
        'user_zone_account_exist': user_zone_account_exist,
    }


@login_required
def create_resource_select_resource_type(request, *args, **kwargs):
    return render_to_response('pages/create-resource.html', context_instance=RequestContext(request))


@login_required
def create_resource(request, *args, **kwargs):
    # Note: This view function must be called by ajax

    ajax_response_data = {'status': 'error', 'message': ''}
    resource_type = request.POST['resource-type']
    res_title = request.POST['title']
    resource_files, full_paths = extract_files_with_paths(request)
    source_names = []
    irods_fnames = request.POST.get('irods_file_names')
    federated = request.POST.get("irods_federated").lower() == 'true'
    auto_aggregate = request.POST.get("auto_aggregate", 'true').lower() == 'true'
    # TODO: need to make REST API consistent with internal API. This is just "move" now there.
    fed_copy_or_move = request.POST.get("copy-or-move")

    if irods_fnames:
        if federated:
            source_names = irods_fnames.split(',')
        else:
            user = request.POST.get('irods-username')
            password = request.POST.get("irods-password")
            port = request.POST.get("irods-port")
            host = request.POST.get("irods-host")
            zone = request.POST.get("irods-zone")
            try:
                upload_from_irods(username=user, password=password, host=host, port=port,
                                  zone=zone, irods_fnames=irods_fnames, res_files=resource_files)
            except utils.ResourceFileSizeException as ex:
                ajax_response_data['message'] = ex.message
                return JsonResponse(ajax_response_data)

            except SessionException as ex:
                ajax_response_data['message'] = ex.stderr
                return JsonResponse(ajax_response_data)

    url_key = "page_redirect_url"
    try:
        _, res_title, metadata, fed_res_path = \
            hydroshare.utils.resource_pre_create_actions(resource_type=resource_type,
                                                         files=resource_files,
                                                         resource_title=res_title,
                                                         source_names=source_names,
                                                         page_redirect_url_key=url_key,
                                                         requesting_user=request.user,
                                                         **kwargs)
    except utils.ResourceFileSizeException as ex:
        ajax_response_data['message'] = ex.message
        return JsonResponse(ajax_response_data)

    except utils.ResourceFileValidationException as ex:
        ajax_response_data['message'] = ex.message
        return JsonResponse(ajax_response_data)

    except Exception as ex:
        ajax_response_data['message'] = ex.message
        return JsonResponse(ajax_response_data)

    try:
        resource = hydroshare.create_resource(
                resource_type=request.POST['resource-type'],
                owner=request.user,
                title=res_title,
                metadata=metadata,
                files=resource_files,
                source_names=source_names,
                # TODO: should probably be resource_federation_path like it is set to.
                fed_res_path=fed_res_path[0] if len(fed_res_path) == 1 else '',
                move=(fed_copy_or_move == 'move'),
                content=res_title, full_paths=full_paths, auto_aggregate=auto_aggregate
        )
    except SessionException as ex:
        ajax_response_data['message'] = ex.stderr
        return JsonResponse(ajax_response_data)
    except Exception as ex:
        ajax_response_data['message'] = ex.message
        return JsonResponse(ajax_response_data)

    try:
        utils.resource_post_create_actions(request=request, resource=resource,
                                           user=request.user, metadata=metadata, **kwargs)
    except (utils.ResourceFileValidationException, Exception) as ex:
        request.session['validation_error'] = ex.message
        ajax_response_data['message'] = ex.message
        ajax_response_data['status'] = 'success'
        ajax_response_data['file_upload_status'] = 'error'
        ajax_response_data['resource_url'] = resource.get_absolute_url()
        return JsonResponse(ajax_response_data)

    request.session['just_created'] = True
    if not ajax_response_data['message']:
        if resource.files.all():
            ajax_response_data['file_upload_status'] = 'success'
        ajax_response_data['status'] = 'success'
        ajax_response_data['resource_url'] = resource.get_absolute_url()

    return JsonResponse(ajax_response_data)


@login_required
def create_user_group(request, *args, **kwargs):
    group_form = GroupCreateForm(request.POST, request.FILES)
    if group_form.is_valid():
        try:
            new_group = group_form.save(request)
            messages.success(request, "Group creation was successful.")
            return HttpResponseRedirect(reverse('group', args=[new_group.id]))
        except IntegrityError as ex:
            if group_form.cleaned_data['name'] in ex.message:
                message = "Group name '{}' already exists".format(group_form.cleaned_data['name'])
                messages.error(request, "Group creation errors: {}.".format(message))
            else:
                messages.error(request, "Group creation errors:{}.".format(ex.message))
    else:
        messages.error(request, "Group creation errors:{}.".format(group_form.errors.as_json))

    return HttpResponseRedirect(request.META['HTTP_REFERER'])


@login_required
def update_user_group(request, group_id, *args, **kwargs):
    user = request.user
    group_to_update = utils.group_from_id(group_id)

    if user.uaccess.can_change_group_flags(group_to_update):
        group_form = GroupUpdateForm(request.POST, request.FILES)
        if group_form.is_valid():
            try:
                group_form.update(group_to_update, request)
                messages.success(request, "Group update was successful.")
            except IntegrityError as ex:
                if group_form.cleaned_data['name'] in ex.message:
                    message = "Group name '{}' already exists".format(group_form.cleaned_data['name'])
                    messages.error(request, "Group update errors: {}.".format(message))
                else:
                    messages.error(request, "Group update errors:{}.".format(ex.message))
        else:
            messages.error(request, "Group update errors:{}.".format(group_form.errors.as_json))
    else:
        messages.error(request, "Group update errors: You don't have permission to update this group")

    return HttpResponseRedirect(request.META['HTTP_REFERER'])

@login_required
def delete_user_group(request, group_id, *args, **kwargs):
    """This one is not really deleting the group object, rather setting the active status
    to False (delete) which can be later restored (undelete) )"""
    try:
        hydroshare.set_group_active_status(request.user, group_id, False)
        messages.success(request, "Group delete was successful.")
    except PermissionDenied:
        messages.error(request, "Group delete errors: You don't have permission to delete"
                                " this group.")

    return HttpResponseRedirect(request.META['HTTP_REFERER'])


@login_required
def restore_user_group(request, group_id, *args, **kwargs):
    """This one is for setting the active status of the group back to True"""
    try:
        hydroshare.set_group_active_status(request.user, group_id, True)
        messages.success(request, "Group restore was successful.")
    except PermissionDenied:
        messages.error(request, "Group restore errors: You don't have permission to restore"
                                " this group.")

    return HttpResponseRedirect(request.META['HTTP_REFERER'])

@login_required
def share_group_with_user(request, group_id, user_id, privilege, *args, **kwargs):
    requesting_user = request.user
    group_to_share = utils.group_from_id(group_id)
    user_to_share_with = utils.user_from_id(user_id)
    if privilege == 'view':
        access_privilege = PrivilegeCodes.VIEW
    elif privilege == 'edit':
        access_privilege = PrivilegeCodes.CHANGE
    elif privilege == 'owner':
        access_privilege = PrivilegeCodes.OWNER
    else:
        access_privilege = PrivilegeCodes.NONE

    if access_privilege != PrivilegeCodes.NONE:
        if requesting_user.uaccess.can_share_group(group_to_share, access_privilege):
            try:
                requesting_user.uaccess.share_group_with_user(group_to_share, user_to_share_with, access_privilege)
                messages.success(request, "User successfully added to the group")
            except PermissionDenied as ex:
                messages.error(request, ex.message)
        else:
            messages.error(request, "You don't have permission to add users to group")
    else:
        messages.error(request, "Invalid privilege for sharing group with user")

    return HttpResponseRedirect(request.META['HTTP_REFERER'])


@login_required
def unshare_group_with_user(request, group_id, user_id, *args, **kwargs):
    """
    Remove a user from a group

    :param request: group owner who is removing the user from the group
    :param group_id: id of the user being removed from the group
    :param user_id: id of the group from which the user to be removed
    :return:
    """
    requesting_user = request.user
    group_to_unshare = utils.group_from_id(group_id)
    user_to_unshare_with = utils.user_from_id(user_id)

    try:
        requesting_user.uaccess.unshare_group_with_user(group_to_unshare, user_to_unshare_with)
        if requesting_user == user_to_unshare_with:
            success_msg = "You successfully left the group."
        else:
            success_msg = "User successfully removed from the group."
        messages.success(request, success_msg)
    except PermissionDenied as ex:
        messages.error(request, ex.message)

    if requesting_user == user_to_unshare_with:
        return HttpResponseRedirect(reverse("my_groups"))
    else:
        return HttpResponseRedirect(request.META['HTTP_REFERER'])


@login_required
def make_group_membership_request(request, group_id, user_id=None, *args, **kwargs):
    """
    Allows either an owner of the group to invite a user to join a group or a user to make a request
    to join a group
    :param request: the user who is making the request
    :param group_id: ID of the group for which the join request/invitation to me made
    :param user_id: needed only when an owner is inviting a user to join a group. This is the id of the user the owner
                    is inviting
    :return:
    """
    requesting_user = request.user
    group_to_join = utils.group_from_id(group_id)
    user_to_join = None
    if user_id is not None:
        user_to_join = utils.user_from_id(user_id)
    try:
        membership_request = requesting_user.uaccess.create_group_membership_request(
            group_to_join, user_to_join)
        if user_to_join is not None:
            message = 'Group membership invitation was successful'
            # send mail to the user who was invited to join group
            send_action_to_take_email(request, user=user_to_join, action_type='group_membership',
                                      group=group_to_join, membership_request=membership_request)
        else:
            message = 'You are now a member of this group'
            # membership_request is None in case where group allows auto approval of membership
            # request. no need send email notification to group owners for membership approval
            if membership_request is not None:
                message = 'Group membership request was successful'
                # send mail to all owners of the group for approval of the request
                for grp_owner in group_to_join.gaccess.owners:
                    send_action_to_take_email(request, user=requesting_user,
                                              action_type='group_membership',
                                              group=group_to_join, group_owner=grp_owner,
                                              membership_request=membership_request)
            else:
                # send mail to all owners of the group to let them know that someone has
                # joined this group
                for grp_owner in group_to_join.gaccess.owners:
                    send_action_to_take_email(request, user=requesting_user,
                                              action_type='group_auto_membership',
                                              group=group_to_join,
                                              group_owner=grp_owner)
        messages.success(request, message)
    except PermissionDenied as ex:
        messages.error(request, ex.message)

    return HttpResponseRedirect(request.META['HTTP_REFERER'])

def group_membership(request, uidb36, token, membership_request_id, **kwargs):
    """
    View for the link in the verification email that was sent to a user
    when they request/invite to join a group.
    User is logged in and the request to join a group is accepted. Then the user is redirected to the group
    profile page of the group for which the membership got accepted.

    :param uidb36: ID of the user to whom the email was sent (part of the link in the email)
    :param token: token that was part of the link in the email
    :param membership_request_id: ID of the GroupMembershipRequest object (part of the link in the email)
    """
    membership_request = GroupMembershipRequest.objects.filter(id=membership_request_id).first()
    if membership_request is not None:
        if membership_request.group_to_join.gaccess.active:
            user = authenticate(uidb36=uidb36, token=token, is_active=True)
            if user is not None:
                user.uaccess.act_on_group_membership_request(membership_request, accept_request=True)
                auth_login(request, user)
                # send email to notify membership acceptance
                _send_email_on_group_membership_acceptance(membership_request)
                if membership_request.invitation_to is not None:
                    message = "You just joined the group '{}'".format(membership_request.group_to_join.name)
                else:
                    message = "User '{}' just joined the group '{}'".format(membership_request.request_from.first_name,
                                                                            membership_request.group_to_join.name)

                messages.info(request, message)
                # redirect to group profile page
                return HttpResponseRedirect('/group/{}/'.format(membership_request.group_to_join.id))
            else:
                messages.error(request, "The link you clicked is no longer valid. Please ask to "
                                        "join the group again.")
                return redirect("/")
        else:
            messages.error(request, "The group is no longer active.")
            return redirect("/")
    else:
        messages.error(request, "The link you clicked is no longer valid.")
        return redirect("/")


@login_required
def act_on_group_membership_request(request, membership_request_id, action, *args, **kwargs):
    """
    Take action (accept or decline) on group membership request

    :param request: requesting user is either owner of the group taking action on a request from a user
                    or a user taking action on a invitation to join a group from a group owner
    :param membership_request_id: id of the membership request object (an instance of GroupMembershipRequest)
                                  to act on
    :param action: need to have a value of either 'accept' or 'decline'
    :return:
    """

    accept_request = action == 'accept'
    user_acting = request.user

    try:
        membership_request = GroupMembershipRequest.objects.get(pk=membership_request_id)
    except ObjectDoesNotExist:
        messages.error(request, 'No matching group membership request was found')
    else:
        if membership_request.group_to_join.gaccess.active:
            try:
                user_acting.uaccess.act_on_group_membership_request(membership_request, accept_request)
                if accept_request:
                    message = 'Membership request accepted'
                    messages.success(request, message)
                    # send email to notify membership acceptance
                    _send_email_on_group_membership_acceptance(membership_request)
                else:
                    message = 'Membership request declined'
                    messages.success(request, message)

            except PermissionDenied as ex:
                messages.error(request, ex.message)
        else:
            messages.error(request, "Group is not active")

    return HttpResponseRedirect(request.META['HTTP_REFERER'])


@login_required
def get_file(request, *args, **kwargs):
    from django_irods.icommands import Session as RodsSession
    name = kwargs['name']
    session = RodsSession("./", "/usr/bin")
    session.runCmd("iinit")
    session.runCmd('iget', [ name, 'tempfile.' + name ])
    return HttpResponse(open(name), content_type='x-binary/octet-stream')


processor_for(GenericResource)(resource_processor)


def get_metadata_terms_page(request, *args, **kwargs):
    return render(request, 'pages/metadata_terms.html')


@login_required
def get_user_or_group_data(request, user_or_group_id, is_group, *args, **kwargs):
    """
    This view function must be called as an AJAX call

    :param user_or_group_id: id of the user or group for which data is needed
    :param is_group : (string) 'false' if the id is for a group, 'true' if id is for a user
    :return: JsonResponse() containing user data
    """
    user_data = {}
    if is_group == 'false':
        user = utils.user_from_id(user_or_group_id)

        if user.userprofile.middle_name:
            user_name = "{} {} {}".format(user.first_name, user.userprofile.middle_name, user.last_name)
        else:
            user_name = "{} {}".format(user.first_name, user.last_name)

        user_data['name'] = user_name
        user_data['email'] = user.email
        user_data['url'] = '{domain}/user/{uid}/'.format(domain=utils.current_site_url(), uid=user.pk)
        if user.userprofile.phone_1:
            user_data['phone'] = user.userprofile.phone_1
        elif user.userprofile.phone_2:
            user_data['phone'] = user.userprofile.phone_2
        else:
            user_data['phone'] = ''

        address = ''
        if user.userprofile.state and user.userprofile.state.lower() != 'unspecified':
            address = user.userprofile.state
        if user.userprofile.country and user.userprofile.country.lower() != 'unspecified':
            if len(address) > 0:
                address += ', ' + user.userprofile.country
            else:
                address = user.userprofile.country

        user_data['address'] = address
        user_data['organization'] = user.userprofile.organization if user.userprofile.organization else ''
        user_data['website'] = user.userprofile.website if user.userprofile.website else ''
        user_data['identifiers'] = user.userprofile.identifiers
    else:
        group = utils.group_from_id(user_or_group_id)
        user_data['organization'] = group.name
        user_data['url'] = '{domain}/user/{uid}/'.format(domain=utils.current_site_url(),
                                                         uid=group.pk)
        user_data['description'] = group.gaccess.description

    return JsonResponse(user_data)


def _send_email_on_group_membership_acceptance(membership_request):
    """
    Sends email notification of group membership acceptance

    :param membership_request: an instance of GroupMembershipRequest class
    :return:
    """

    if membership_request.invitation_to is not None:
        # user accepted invitation from the group owner
        # here we are sending email to group owner who invited
        email_msg = """Dear {}
        <p>Your invitation to user '{}' to join the group '{}' has been accepted.</p>
        <p>Thank you</p>
        <p>The HydroShare Team</p>
        """.format(membership_request.request_from.first_name,
                   membership_request.invitation_to.first_name, membership_request.group_to_join.name)
    else:
        # group owner accepted user request
        # here wre are sending email to the user whose request to join got accepted
        email_msg = """Dear {}
        <p>Your request to join the group '{}' has been accepted.</p>
        <p>Thank you</p>
        <p>The HydroShare Team</p>
        """.format(membership_request.request_from.first_name, membership_request.group_to_join.name)

    send_mail(subject="HydroShare group membership",
              message=email_msg,
              html_message=email_msg,
              from_email=settings.DEFAULT_FROM_EMAIL,
              recipient_list=[membership_request.request_from.email])


def _share_resource_with_user(request, frm, resource, requesting_user, privilege):
    if frm.is_valid():
        try:
            requesting_user.uaccess.share_resource_with_user(resource, frm.cleaned_data['user'], privilege)
        except PermissionDenied as exp:
            messages.error(request, exp.message)
    else:
        messages.error(request, frm.errors.as_json())


def _unshare_resource_with_users(request, requesting_user, users_to_unshare_with, resource, privilege):
    users_to_keep = User.objects.in_bulk(users_to_unshare_with).values()
    owners = set(resource.raccess.owners.all())
    editors = set(resource.raccess.edit_users.all()) - owners
    viewers = set(resource.raccess.view_users.all()) - editors - owners

    if privilege == 'owner':
        all_shared_users = owners
    elif privilege == 'edit':
        all_shared_users = editors
    elif privilege == 'view':
        all_shared_users = viewers
    else:
        all_shared_users = []

    go_to_resource_listing_page = False
    for user in all_shared_users:
        if user not in users_to_keep:
            try:
                # requesting user is the resource owner or requesting_user is self unsharing
                # COUCH: no need for undo_share; doesn't do what is intended 11/19/2016
                requesting_user.uaccess.unshare_resource_with_user(resource, user)

                if requesting_user == user and not resource.raccess.public:
                    go_to_resource_listing_page = True
            except PermissionDenied as exp:
                messages.error(request, exp.message)
                break
    return go_to_resource_listing_page


def _set_resource_sharing_status(request, user, resource, flag_to_set, flag_value):
    """
    Set flags 'public', 'discoverable', 'shareable'

    This routine generates appropriate messages for the REST API and thus differs from
    AbstractResource.set_public, set_discoverable, which raise exceptions.
    """

    if flag_to_set == 'shareable':  # too simple to deserve a method in AbstractResource
        # access control is separate from validation logic
        if not user.uaccess.can_change_resource_flags(resource):
            messages.error(request, "You don't have permission to change resource sharing status")
            return
        if resource.raccess.shareable != flag_value:
            resource.raccess.shareable = flag_value
            resource.raccess.save()
            return

    elif flag_to_set == 'discoverable':
        try:
            resource.set_discoverable(flag_value, user)  # checks access control
        except ValidationError as v:
            messages.error(request, v.message)

    elif flag_to_set == 'public':
        try:
            resource.set_public(flag_value, user)  # checks access control
        except ValidationError as v:
            messages.error(request, v.message)

    else:
        messages.error(request,
                       "unrecognized resource flag {}".format(flag_to_set))


def _get_message_for_setting_resource_flag(has_files, has_metadata, resource_flag):
    msg = ''
    if not has_metadata and not has_files:
        msg = "Resource does not have sufficient required metadata and content files to be {flag}".format(
              flag=resource_flag)
    elif not has_metadata:
        msg = "Resource does not have sufficient required metadata to be {flag}".format(flag=resource_flag)
    elif not has_files:
        msg = "Resource does not have required content files to be {flag}".format(flag=resource_flag)

    return msg


class MyGroupsView(TemplateView):
    template_name = 'pages/my-groups.html'

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(MyGroupsView, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        u = User.objects.get(pk=self.request.user.id)

        groups = u.uaccess.view_groups
        group_membership_requests = GroupMembershipRequest.objects.filter(invitation_to=u).exclude(
            group_to_join__gaccess__active=False).all()
        # for each group object, set a dynamic attribute to know if the user owns the group
        for g in groups:
            g.is_group_owner = u.uaccess.owns_group(g)

        active_groups = [g for g in groups if g.gaccess.active]
        inactive_groups = [g for g in groups if not g.gaccess.active]
        my_pending_requests = GroupMembershipRequest.objects.filter(request_from=u).exclude(
            group_to_join__gaccess__active=False)
        return {
            'profile_user': u,
            'groups': active_groups,
            'inactive_groups': inactive_groups,
            'my_pending_requests': my_pending_requests,
            'group_membership_requests': group_membership_requests
        }


class AddUserForm(forms.Form):
        user = forms.ModelChoiceField(User.objects.all(), widget=autocomplete_light.ChoiceWidget("UserAutocomplete"))


class GroupView(TemplateView):
    template_name = 'pages/group.html'

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(GroupView, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        group_id = kwargs['group_id']
        g = Group.objects.get(pk=group_id)
        u = User.objects.get(pk=self.request.user.id)
        u.is_group_owner = u.uaccess.owns_group(g)
        u.is_group_editor = g in u.uaccess.edit_groups
        u.is_group_viewer = g in u.uaccess.view_groups

        g.join_request_waiting_owner_action = g.gaccess.group_membership_requests.filter(request_from=u).exists()
        g.join_request_waiting_user_action = g.gaccess.group_membership_requests.filter(invitation_to=u).exists()
        g.join_request = g.gaccess.group_membership_requests.filter(invitation_to=u).first()

        group_resources = []
        # for each of the resources this group has access to, set resource dynamic
        # attributes (grantor - group member who granted access to the resource) and (date_granted)
        for res in g.gaccess.view_resources:
            grp = GroupResourcePrivilege.objects.get(resource=res, group=g)
            res.grantor = grp.grantor
            res.date_granted = grp.start
            group_resources.append(res)

        # TODO: need to sort this resource list using the date_granted field

        return {
            'profile_user': u,
            'group': g,
            'view_users': g.gaccess.get_users_with_explicit_access(PrivilegeCodes.VIEW),
            'group_resources': group_resources,
            'add_view_user_form': AddUserForm(),
        }


class CollaborateView(TemplateView):
    template_name = 'pages/collaborate.html'

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(CollaborateView, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        u = User.objects.get(pk=self.request.user.id)
        groups = Group.objects.filter(gaccess__active=True).exclude(name="Hydroshare Author")
        # for each group set group dynamic attributes
        for g in groups:
            g.is_user_member = u in g.gaccess.members
            g.join_request_waiting_owner_action = g.gaccess.group_membership_requests.filter(request_from=u).exists()
            g.join_request_waiting_user_action = g.gaccess.group_membership_requests.filter(invitation_to=u).exists()
            g.join_request = None
            if g.join_request_waiting_owner_action or g.join_request_waiting_user_action:
                g.join_request = g.gaccess.group_membership_requests.filter(request_from=u).first() or \
                                 g.gaccess.group_membership_requests.filter(invitation_to=u).first()
        return {
            'profile_user': u,
            'groups': groups,
        }
