from __future__ import absolute_import
import json
import datetime
import pytz
import logging

from django.core.mail import send_mail
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group, User
from django.contrib.sites.models import Site
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.core.exceptions import ValidationError, PermissionDenied, ObjectDoesNotExist
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render_to_response, render, redirect
from django.template import RequestContext
from django.core import signing
from django.db import Error, IntegrityError
from django import forms
from django.views.generic import TemplateView
from django.core.urlresolvers import reverse

from rest_framework.decorators import api_view

from mezzanine.conf import settings
from mezzanine.pages.page_processors import processor_for
import autocomplete_light
from inplaceeditform.commons import get_dict_from_obj, apply_filters
from inplaceeditform.views import _get_http_response, _get_adaptor
from django_irods.storage import IrodsStorage
from django_irods.icommands import SessionException

from hs_core import hydroshare
from hs_core.hydroshare.utils import get_resource_by_shortkey, resource_modified
from .utils import authorize, upload_from_irods, ACTION_TO_AUTHORIZE, run_script_to_update_hyrax_input_files, \
    get_my_resources_list, send_action_to_take_email
from hs_core.models import GenericResource, resource_processor, CoreMetaData, Relation
from hs_core.hydroshare.resource import METADATA_STATUS_SUFFICIENT, METADATA_STATUS_INSUFFICIENT
from hs_core.tasks import create_bag_by_irods

from . import resource_rest_api
from . import user_rest_api

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


def add_file_to_resource(request, shortkey, *args, **kwargs):
    resource, _, _ = authorize(request, shortkey, needed_permission=ACTION_TO_AUTHORIZE.EDIT_RESOURCE)
    res_files = request.FILES.getlist('files')
    extract_metadata = request.REQUEST.get('extract-metadata', 'No')
    extract_metadata = True if extract_metadata.lower() == 'yes' else False

    try:
        utils.resource_file_add_pre_process(resource=resource, files=res_files, user=request.user,
                                            extract_metadata=extract_metadata)

    except hydroshare.utils.ResourceFileSizeException as ex:
        request.session['file_size_error'] = ex.message
        return HttpResponseRedirect(request.META['HTTP_REFERER'])

    except (hydroshare.utils.ResourceFileValidationException, Exception) as ex:
        request.session['validation_error'] = ex.message
        return HttpResponseRedirect(request.META['HTTP_REFERER'])

    try:
        hydroshare.utils.resource_file_add_process(resource=resource, files=res_files, user=request.user,
                                                   extract_metadata=extract_metadata)

    except (hydroshare.utils.ResourceFileValidationException, Exception) as ex:
        request.session['validation_error'] = ex.message

    return HttpResponseRedirect(request.META['HTTP_REFERER'])


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


def is_multiple_file_allowed_for_resource_type(request, resource_type, *args, **kwargs):
    resource_cls = hydroshare.check_resource_type(resource_type)
    if request.is_ajax:
        # TODO: use try catch
        ajax_response_data = {'allow_multiple_file': resource_cls.can_have_multiple_files()}
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
    res.extra_metadata = post_data.dict()
    is_update_success = True
    err_message = ""
    try:
        res.save()
    except Error as ex:
        is_update_success = False
        err_message = ex.message

    if is_update_success:
        resource_modified(res, request.user)

    if request.is_ajax():
        if is_update_success:
            ajax_response_data = {'status': 'success'}
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


def add_metadata_element(request, shortkey, element_name, *args, **kwargs):
    res, _, _ = authorize(request, shortkey, needed_permission=ACTION_TO_AUTHORIZE.EDIT_RESOURCE)

    sender_resource = _get_resource_sender(element_name, res)
    handler_response = pre_metadata_element_create.send(sender=sender_resource, element_name=element_name,
                                                        request=request)
    is_add_success = False
    err_msg = "Failed to create metadata element '{}'. {}."
    for receiver, response in handler_response:
        if 'is_valid' in response:
            if response['is_valid']:
                element_data_dict = response['element_data_dict']
                if element_name == 'subject':
                    keywords = [k.strip() for k in element_data_dict['value'].split(',')]
                    if res.metadata.subjects.all().count() > 0:
                        res.metadata.subjects.all().delete()
                    for kw in keywords:
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

                if is_add_success:
                    resource_modified(res, request.user)

    if request.is_ajax():
        if is_add_success:
            if res.metadata.has_all_required_elements():
                metadata_status = METADATA_STATUS_SUFFICIENT
            else:
                metadata_status = METADATA_STATUS_INSUFFICIENT

            if element_name == 'subject':
                ajax_response_data = {'status': 'success', 'element_name': element_name, 'metadata_status': metadata_status}
            else:
                ajax_response_data = {'status': 'success', 'element_id': element.id, 'element_name': element_name, 'metadata_status': metadata_status}

            return HttpResponse(json.dumps(ajax_response_data))

        else:
            ajax_response_data = {'status': 'error', 'message': err_msg}
            return HttpResponse (json.dumps(ajax_response_data))

    if 'resource-mode' in request.POST:
        request.session['resource-mode'] = 'edit'

    return HttpResponseRedirect(request.META['HTTP_REFERER'])


def update_metadata_element(request, shortkey, element_name, element_id, *args, **kwargs):
    res, _, _ = authorize(request, shortkey, needed_permission=ACTION_TO_AUTHORIZE.EDIT_RESOURCE)
    sender_resource = _get_resource_sender(element_name, res)
    handler_response = pre_metadata_element_update.send(sender=sender_resource, element_name=element_name,
                                                        element_id=element_id, request=request)
    is_update_success = False
    err_msg = "Failed to update metadata element '{}'. {}."
    for receiver, response in handler_response:
        if 'is_valid' in response:
            if response['is_valid']:
                element_data_dict = response['element_data_dict']
                try:
                    res.metadata.update_element(element_name, element_id, **element_data_dict)
                    is_update_success = True
                except ValidationError as exp:
                    err_msg = err_msg.format(element_name, exp.message)
                    request.session['validation_error'] = err_msg
                except Error as exp:
                    # some database error occurred
                    err_msg = err_msg.format(element_name, exp.message)
                    request.session['validation_error'] = err_msg
                if element_name == 'title':
                    if res.raccess.public:
                        if not res.can_be_public_or_discoverable:
                            res.raccess.public = False
                            res.raccess.save()

                if is_update_success:
                    resource_modified(res, request.user)

    if request.is_ajax():
        if is_update_success:
            if res.metadata.has_all_required_elements():
                metadata_status = METADATA_STATUS_SUFFICIENT
            else:
                metadata_status = METADATA_STATUS_INSUFFICIENT

            ajax_response_data = {'status': 'success', 'element_name': element_name, 'metadata_status': metadata_status}
            return HttpResponse(json.dumps(ajax_response_data))
        else:
            ajax_response_data = {'status': 'error', 'message': err_msg}
            return HttpResponse(json.dumps(ajax_response_data))

    if 'resource-mode' in request.POST:
        request.session['resource-mode'] = 'edit'

    return HttpResponseRedirect(request.META['HTTP_REFERER'])


@api_view(['GET'])
def file_download_url_mapper(request, shortkey):
    """ maps the file URIs in resourcemap document to django_irods download view function"""

    authorize(request, shortkey, needed_permission=ACTION_TO_AUTHORIZE.VIEW_RESOURCE)
    irods_file_path = '/'.join(request.path.split('/')[2:-1])
    istorage = IrodsStorage()
    file_download_url = istorage.url(irods_file_path)
    return HttpResponseRedirect(file_download_url)


def delete_metadata_element(request, shortkey, element_name, element_id, *args, **kwargs):
    res, _, _ = authorize(request, shortkey, needed_permission=ACTION_TO_AUTHORIZE.EDIT_RESOURCE)
    res.metadata.delete_element(element_name, element_id)
    resource_modified(res, request.user)
    request.session['resource-mode'] = 'edit'
    return HttpResponseRedirect(request.META['HTTP_REFERER'])


def delete_file(request, shortkey, f, *args, **kwargs):
    res, _, user = authorize(request, shortkey, needed_permission=ACTION_TO_AUTHORIZE.EDIT_RESOURCE)
    hydroshare.delete_resource_file(shortkey, f, user)

    return HttpResponseRedirect(request.META['HTTP_REFERER'])


def delete_resource(request, shortkey, *args, **kwargs):
    res, _, user = authorize(request, shortkey, needed_permission=ACTION_TO_AUTHORIZE.DELETE_RESOURCE)

    res_title = res.metadata.title
    res_id = shortkey
    res_type = res.resource_type
    resource_related_collections = [col for col in res.collections.all()]

    try:
        hydroshare.delete_resource(shortkey)
    except ValidationError as ex:
        request.session['validation_error'] = ex.message
        return HttpResponseRedirect(request.META['HTTP_REFERER'])

    # if the deleted resource is part of any collection resource, then for each of those collection
    # create a CollectionDeletedResource object which can then be used to list collection deleted
    # resources on collection resource landing page
    for collection_res in resource_related_collections:
        CollectionDeletedResource.objects.create(resource_title=res_title,
                                                 deleted_by=user,
                                                 resource_id=res_id,
                                                 resource_type=res_type,
                                                 collection=collection_res)

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
        task_id = utils.replicate_resource_bag_to_user_zone(user, shortkey)
        if task_id:
            result = create_bag_by_irods.AsyncResult(task_id)
            result_output = result.wait(timeout=None, interval=0.5)
            if result_output:
                # replicate resource bag now that the bag is created
                utils.replicate_resource_bag_to_user_zone(user, shortkey)

        return HttpResponse(
            json.dumps({"success": "This resource bag zip file has been successfully replicated to your iRODS user zone."}),
            content_type = "application/json"
        )
    except SessionException as ex:
        return HttpResponse(
        json.dumps({"error": ex.stderr}),
        content_type="application/json"
        )

def create_new_version_resource(request, shortkey, *args, **kwargs):
    res, authorized, user = authorize(request, shortkey, needed_permission=ACTION_TO_AUTHORIZE.CREATE_RESOURCE_VERSION)

    if res.locked_time:
        elapsed_time = datetime.datetime.now(pytz.utc) - res.locked_time
        if elapsed_time.days >= 0 or elapsed_time.seconds > settings.RESOURCE_LOCK_TIMEOUT_SECONDS:
            # clear the lock since the elapsed time is greater than timeout threshold
            res.locked_time = None
            res.save()
        else:
            # cannot create new version for this resource since the resource is locked by another user
            request.session['new_version_resource_creation_error'] = 'Failed to create a new version for ' \
                                                                     'this resource since another user is creating a ' \
                                                                     'new version for this resource synchronously.'
            return HttpResponseRedirect(res.get_absolute_url())

    new_resource = None
    try:
        # lock the resource to prevent concurrent new version creation since only one new version for an
        # obsoleted resource is allowed
        res.locked_time = datetime.datetime.now(pytz.utc)
        res.save()
        new_resource = hydroshare.create_new_version_empty_resource(shortkey, user)
        new_resource = hydroshare.create_new_version_resource(res, new_resource, user)
    except Exception as ex:
        if new_resource:
            new_resource.delete()
        # release the lock if new version of the resource failed to create
        res.locked_time = None
        res.save()
        request.session['new_version_resource_creation_error'] = ex.message
        return HttpResponseRedirect(res.get_absolute_url())

    # release the lock if new version of the resource is created successfully
    res.locked_time = None
    res.save()

    # go to resource landing page
    request.session['just_created'] = True
    return HttpResponseRedirect(new_resource.get_absolute_url())


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
    t = request.POST['t']
    if t == 'make_public':
        _set_resource_sharing_status(request, user, res, flag_to_set='public', flag_value=True)
    elif t == 'make_private' or t == 'make_not_discoverable':
        _set_resource_sharing_status(request, user, res, flag_to_set='public', flag_value=False)
    elif t == 'make_discoverable':
        _set_resource_sharing_status(request, user, res, flag_to_set='discoverable', flag_value=True)
    elif t == 'make_not_shareable':
        _set_resource_sharing_status(request, user, res, flag_to_set='shareable', flag_value=False)
    elif t == 'make_shareable':
       _set_resource_sharing_status(request, user, res, flag_to_set='shareable', flag_value=True)

    return HttpResponseRedirect(request.META['HTTP_REFERER'])


def share_resource_with_user(request, shortkey, privilege, user_id, *args, **kwargs):
    return _share_resource(request, shortkey, privilege, user_id, user_or_group='user')


def share_resource_with_group(request, shortkey, privilege, group_id, *args, **kwargs):
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
    res, _, user = authorize(request, shortkey, needed_permission=ACTION_TO_AUTHORIZE.VIEW_RESOURCE)
    user_to_unshare_with = utils.user_from_id(user_id)

    try:
        if user.uaccess.can_unshare_resource_with_user(res, user_to_unshare_with):
            # requesting user is the resource owner or user is self unsharing (user is user_to_unshare_with)
            user.uaccess.unshare_resource_with_user(res, user_to_unshare_with)
        else:
            # requesting user is the original grantor of privilege to user_to_unshare_with
            # COUCH: This can raise a PermissionDenied exception without a guard such as
            # user.uaccess.can_undo_share_resource_with_user(res, user_to_unshare_with)
            user.uaccess.undo_share_resource_with_user(res, user_to_unshare_with)

        messages.success(request, "Resource unsharing was successful")
        if not user.uaccess.can_view_resource(res):
            # user has no access to the resource - redirect to resource listing page
            return HttpResponseRedirect('/my-resources/')
    except PermissionDenied as exp:
        messages.error(request, exp.message)

    return HttpResponseRedirect(request.META['HTTP_REFERER'])


def unshare_resource_with_group(request, shortkey, group_id, *args, **kwargs):
    res, _, user = authorize(request, shortkey, needed_permission=ACTION_TO_AUTHORIZE.VIEW_RESOURCE)
    group_to_unshare_with = utils.group_from_id(group_id)

    try:
        if user.uaccess.can_unshare_resource_with_group(res, group_to_unshare_with):
            # requesting user is the resource owner or admin
            user.uaccess.unshare_resource_with_group(res, group_to_unshare_with)
        else:
            # requesting user is the original grantor of privilege to group_to_unshare_with
            user.uaccess.undo_share_resource_with_group(res, group_to_unshare_with)

        messages.success(request, "Resource unsharing was successful")
        if not user.uaccess.can_view_resource(res):
            # user has no access to the resource - redirect to resource listing page
            return HttpResponseRedirect('/my-resources/')
    except PermissionDenied as exp:
        messages.error(request, exp.message)

    return HttpResponseRedirect(request.META['HTTP_REFERER'])

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
                                                      purpose=frm_data['purpose'])
        if 'picture' in request.FILES:
            new_group.gaccess.picture = request.FILES['picture']

        privacy_level = frm_data['privacy_level']
        self._set_privacy_level(new_group, privacy_level)
        return new_group


class GroupUpdateForm(GroupForm):
    active = forms.CharField(required=False)

    def clean_active(self):
        data = self.cleaned_data['active']
        if data not in ('on', ''):
            raise forms.ValidationError("Invalid active value.")
        return data

    def update(self, group_to_update, request):
        frm_data = self.cleaned_data
        group_to_update.name = frm_data['name']
        group_to_update.save()
        group_to_update.gaccess.description = frm_data['description']
        group_to_update.gaccess.purpose = frm_data['purpose']
        group_to_update.gaccess.active = frm_data['active'] == 'on'
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
    in_production, user_zone_account_exist = utils.get_user_zone_status_info(user)

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
    resource_type = request.POST['resource-type']
    res_title = request.POST['title']

    resource_files = request.FILES.getlist('files')
    fed_res_file_names=[]
    irods_fnames = request.POST.get('irods_file_names')
    federated = request.POST.get("irods_federated").lower()=='true'
    fed_copy_or_move = request.POST.get("copy-or-move")

    if irods_fnames:
        if federated:
            fed_res_file_names = irods_fnames.split(',')
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
                context = {'file_size_error': ex.message}
                return render_to_response('pages/create-resource.html', context, context_instance=RequestContext(request))
            except SessionException as ex:
                context = {'resource_creation_error': ex.stderr}
                return render_to_response('pages/create-resource.html', context, context_instance=RequestContext(request))

    url_key = "page_redirect_url"

    try:
        page_url_dict, res_title, metadata, fed_res_path = hydroshare.utils.resource_pre_create_actions(resource_type=resource_type, files=resource_files,
                                                                    resource_title=res_title, fed_res_file_names=fed_res_file_names,
                                                                    page_redirect_url_key=url_key, requesting_user=request.user, **kwargs)
    except utils.ResourceFileSizeException as ex:
        context = {'file_size_error': ex.message}
        return render_to_response('pages/create-resource.html', context, context_instance=RequestContext(request))

    except utils.ResourceFileValidationException as ex:
        context = {'validation_error': ex.message}
        return render_to_response('pages/create-resource.html', context, context_instance=RequestContext(request))

    except Exception as ex:
        context = {'resource_creation_error': ex.message}
        return render_to_response('pages/create-resource.html', context, context_instance=RequestContext(request))

    if url_key in page_url_dict:
        return render(request, page_url_dict[url_key], {'title': res_title, 'metadata': metadata})

    # try:
    resource = hydroshare.create_resource(
            resource_type=request.POST['resource-type'],
            owner=request.user,
            title=res_title,
            metadata=metadata,
            files=resource_files,
            fed_res_file_names=fed_res_file_names,
            fed_res_path = fed_res_path[0] if len(fed_res_path)==1 else '',
            fed_copy_or_move=fed_copy_or_move,
            content=res_title
    )
    # except Exception as ex:
    #     context = {'resource_creation_error': ex.message }
    #     return render_to_response('pages/create-resource.html', context, context_instance=RequestContext(request))

    try:
        utils.resource_post_create_actions(resource=resource, user=request.user, metadata=metadata, **kwargs)
    except (utils.ResourceFileValidationException, Exception) as ex:
        request.session['validation_error'] = ex.message

    # go to resource landing page
    request.session['just_created'] = True

    return HttpResponseRedirect(resource.get_absolute_url())


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
        membership_request = requesting_user.uaccess.create_group_membership_request(group_to_join, user_to_join)
        if user_to_join is not None:
            message = 'Group membership invitation was successful'
            # send mail to the user who was invited to join group
            send_action_to_take_email(request, user=user_to_join, action_type='group_membership',
                                      group=group_to_join, membership_request=membership_request)
        else:
            message = 'Group membership request was successful'
            # send mail to all owners of the group
            for grp_owner in group_to_join.gaccess.owners:
                send_action_to_take_email(request, user=requesting_user, action_type='group_membership',
                                          group=group_to_join, group_owner=grp_owner,
                                          membership_request=membership_request)

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
                messages.error(request, "The link you clicked is no longer valid.")
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
                    messages.error(request, message)

            except PermissionDenied as ex:
                messages.error(request, ex.message)
        else:
            messages.error(request, "Group is not active")

    return HttpResponseRedirect(request.META['HTTP_REFERER'])


@login_required
def get_file(request, *args, **kwargs):
    from django_irods.icommands import RodsSession
    name = kwargs['name']
    session = RodsSession("./", "/usr/bin")
    session.runCmd("iinit");
    session.runCmd('iget', [ name, 'tempfile.' + name ])
    return HttpResponse(open(name), content_type='x-binary/octet-stream')


processor_for(GenericResource)(resource_processor)


def get_metadata_terms_page(request, *args, **kwargs):
    return render(request, 'pages/metadata_terms.html')


@login_required
def get_user_data(request, user_id, *args, **kwargs):
    """
    This view function must be called as an AJAX call

    :param user_id: id if the user for whom data is needed
    :return: JsonResponse() containing user data
    """
    user = utils.user_from_id(user_id)

    if user.userprofile.middle_name:
        user_name = "{} {} {}".format(user.first_name, user.userprofile.middle_name, user.last_name)
    else:
        user_name = "{} {}".format(user.first_name, user.last_name)

    user_data = {'name': user_name, 'email': user.email}
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
                if requesting_user.uaccess.can_unshare_resource_with_user(resource, user):
                    # requesting user is the resource owner or requesting_user is self unsharing
                    requesting_user.uaccess.unshare_resource_with_user(resource, user)
                else:
                    # requesting user is the original grantor of privilege to user
                    # TODO from @alvacouch: This can raise a PermissionDenied exception without a guard such as
                    # user.uaccess.can_undo_share_resource_with_user(res, user_to_unshare_with)
                    requesting_user.uaccess.undo_share_resource_with_user(resource, user)

                if requesting_user == user and not resource.raccess.public:
                    go_to_resource_listing_page = True
            except PermissionDenied as exp:
                messages.error(request, exp.message)
                break
    return go_to_resource_listing_page


def _set_resource_sharing_status(request, user, resource, flag_to_set, flag_value):
    if not user.uaccess.can_change_resource_flags(resource):
        messages.error(request, "You don't have permission to change resource sharing status")
        return

    if flag_to_set == 'shareable':
        if resource.raccess.shareable != flag_value:
            resource.raccess.shareable = flag_value
            resource.raccess.save()
            return

    has_files = False
    has_metadata = False
    can_resource_be_public_or_discoverable = False
    is_public = (flag_to_set == 'public' and flag_value)
    is_discoverable = (flag_to_set == 'discoverable' and flag_value)
    if is_public or is_discoverable:
        has_files = resource.has_required_content_files()
        has_metadata = resource.metadata.has_all_required_elements()
        can_resource_be_public_or_discoverable = has_files and has_metadata

    if is_public and not can_resource_be_public_or_discoverable:
        messages.error(request, _get_message_for_setting_resource_flag(has_files, has_metadata, resource_flag='public'))
    else:
        if is_discoverable:
            if can_resource_be_public_or_discoverable:
                resource.raccess.public = False
                resource.raccess.discoverable = True
            else:
                messages.error(request, _get_message_for_setting_resource_flag(has_files, has_metadata,
                                                                               resource_flag='discoverable'))
        else:
            resource.raccess.public = is_public
            resource.raccess.discoverable = is_public

        resource.raccess.save()
        # set isPublic metadata AVU accordingly
        if resource.resource_federation_path:
            istorage = IrodsStorage('federated')
            res_coll = '{}/{}'.format(resource.resource_federation_path, resource.short_id)
        else:
            istorage = IrodsStorage()
            res_coll = resource.short_id
        istorage.setAVU(res_coll, "isPublic", str(resource.raccess.public))

        # run script to update hyrax input files when a private netCDF resource is made public
        if flag_to_set=='public' and flag_value and settings.RUN_HYRAX_UPDATE and resource.resource_type=='NetcdfResource':
            run_script_to_update_hyrax_input_files()


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
        group_membership_requests = GroupMembershipRequest.objects.filter(invitation_to=u).exclude(group_to_join__gaccess__active=False).all()
        # for each group object, set a dynamic attribute to know if the user owns the group
        for g in groups:
            g.is_group_owner = u.uaccess.owns_group(g)

        return {
            'profile_user': u,
            'groups': groups,
            'my_pending_requests': GroupMembershipRequest.objects.filter(request_from=u).exclude(group_to_join__gaccess__active=False),
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
            grp = GroupResourcePrivilege.objects.filter(resource=res, group=g).first()
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
