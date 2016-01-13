from __future__ import absolute_import
import json

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group, User
from django.contrib.sites.models import Site
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import get_object_or_404, render_to_response, render
from django.core import exceptions as ex
from django.template import RequestContext
from django.core import signing
from django import forms

from rest_framework.decorators import api_view

from mezzanine.conf import settings
from mezzanine.pages.page_processors import processor_for
import autocomplete_light
from inplaceeditform.commons import get_dict_from_obj, apply_filters
from inplaceeditform.views import _get_http_response, _get_adaptor
from django_irods.storage import IrodsStorage
from hs_access_control.models import PrivilegeCodes, HSAccessException

from django_irods.icommands import SessionException
from hs_core import hydroshare
from hs_core.hydroshare import get_resource_list
from hs_core.hydroshare.utils import get_resource_by_shortkey, resource_modified
from .utils import authorize, upload_from_irods
from hs_core.models import BaseResource, GenericResource, resource_processor, CoreMetaData

from . import resource_rest_api
from . import user_rest_api

from hs_core.hydroshare import utils
from . import utils as view_utils
from hs_core.signals import *


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
    resource, _, _ = authorize(request, shortkey, edit=True, full=True, superuser=True)
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


def add_metadata_element(request, shortkey, element_name, *args, **kwargs):
    res, _, _ = authorize(request, shortkey, edit=True, full=True, superuser=True)

    sender_resource = _get_resource_sender(element_name, res)
    handler_response = pre_metadata_element_create.send(sender=sender_resource, element_name=element_name,
                                                        request=request)
    is_add_success = False
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
                else:
                    try:
                        element = res.metadata.create_element(element_name, **element_data_dict)
                    except ValidationError as exp:
                        request.session['validation_error'] = exp.message
                is_add_success = True
                resource_modified(res, request.user)

    if request.is_ajax():
        if is_add_success:
            if res.metadata.has_all_required_elements():
                metadata_status = "Sufficient to make public"
            else:
                metadata_status = "Insufficient to make public"

            if element_name == 'subject':
                ajax_response_data = {'status': 'success', 'element_name': element_name, 'metadata_status': metadata_status}
            else:
                ajax_response_data = {'status': 'success', 'element_id': element.id, 'element_name': element_name, 'metadata_status': metadata_status}

            return HttpResponse(json.dumps(ajax_response_data))

        else:
            ajax_response_data = {'status': 'error'}
            return HttpResponse (json.dumps(ajax_response_data))

    if 'resource-mode' in request.POST:
        request.session['resource-mode'] = 'edit'

    return HttpResponseRedirect(request.META['HTTP_REFERER'])


def update_metadata_element(request, shortkey, element_name, element_id, *args, **kwargs):
    res, _, _ = authorize(request, shortkey, edit=True, full=True, superuser=True)
    sender_resource = _get_resource_sender(element_name, res)
    handler_response = pre_metadata_element_update.send(sender=sender_resource, element_name=element_name,
                                                        element_id=element_id, request=request)
    is_update_success = False

    for receiver, response in handler_response:
        if 'is_valid' in response:
            if response['is_valid']:
                element_data_dict = response['element_data_dict']
                try:
                    res.metadata.update_element(element_name, element_id, **element_data_dict)
                except ValidationError as exp:
                    request.session['validation_error'] = exp.message
                if element_name == 'title':
                    if res.raccess.public:
                        if not res.can_be_public_or_discoverable:
                            res.raccess.public = False
                            res.raccess.save()

                resource_modified(res, request.user)
                is_update_success = True

    if request.is_ajax():
        if is_update_success:
            if res.metadata.has_all_required_elements():
                metadata_status = "Sufficient to make public"
            else:
                metadata_status = "Insufficient to make public"

            ajax_response_data = {'status': 'success', 'element_name': element_name, 'metadata_status': metadata_status}
            return HttpResponse(json.dumps(ajax_response_data))
        else:
            ajax_response_data = {'status': 'error'}
            return HttpResponse(json.dumps(ajax_response_data))

    return HttpResponseRedirect(request.META['HTTP_REFERER'])


@api_view(['GET'])
def file_download_url_mapper(request, shortkey, filename):
    """ maps the file URIs in resourcemap document to django_irods download view function"""

    authorize(request, shortkey, view=True, edit=True, full=True, superuser=True)
    irods_file_path = '/'.join(request.path.split('/')[2:-1])
    istorage = IrodsStorage()
    file_download_url = istorage.url(irods_file_path)
    return HttpResponseRedirect(file_download_url)


def delete_metadata_element(request, shortkey, element_name, element_id, *args, **kwargs):
    res, _, _ = authorize(request, shortkey, edit=True, full=True, superuser=True)
    res.metadata.delete_element(element_name, element_id)
    resource_modified(res, request.user)
    request.session['resource-mode'] = 'edit'
    return HttpResponseRedirect(request.META['HTTP_REFERER'])


def delete_file(request, shortkey, f, *args, **kwargs):
    res, _, user = authorize(request, shortkey, edit=True, full=True, superuser=True)
    hydroshare.delete_resource_file(shortkey, f, user)

    return HttpResponseRedirect(request.META['HTTP_REFERER'])


def delete_resource(request, shortkey, *args, **kwargs):
    res, _, _ = authorize(request, shortkey, edit=True, full=True, superuser=True)

    res.delete()
    return HttpResponseRedirect('/my-resources/')


def publish(request, shortkey, *args, **kwargs):
    res, _, _ = authorize(request, shortkey, edit=True, full=True, superuser=True)

    hydroshare.publish_resource(shortkey)
    resource_modified(res, request.user)
    return HttpResponseRedirect(request.META['HTTP_REFERER'])


# TOD0: this view function needs refactoring once the new access control UI works
def change_permissions(request, shortkey, *args, **kwargs):

    class AddUserForm(forms.Form):
        user = forms.ModelChoiceField(User.objects.all(), widget=autocomplete_light.ChoiceWidget("UserAutocomplete"))

    class AddGroupForm(forms.Form):
        group = forms.ModelChoiceField(Group.objects.all(), widget=autocomplete_light.ChoiceWidget("GroupAutocomplete"))

    res, _, user = authorize(request, shortkey, edit=True, full=True, superuser=True)
    t = request.POST['t']
    values = [int(k) for k in request.POST.getlist('designees', [])]
    go_to_resource_listing_page = False
    if t == 'owners':
        go_to_resource_listing_page = _unshare_resource_with_users(request, user, values, res, 'owner')
    elif t == 'edit_users':
        go_to_resource_listing_page = _unshare_resource_with_users(request, user, values, res, 'edit')
    # elif t == 'edit_groups':
    #     res.edit_groups = Group.objects.in_bulk(values)
    elif t == 'view_users':
        go_to_resource_listing_page = _unshare_resource_with_users(request, user, values, res, 'view')
    # elif t == 'view_groups':
    #     res.view_groups = Group.objects.in_bulk(values)
    elif t == 'add_view_user':
        frm = AddUserForm(data=request.POST)
        _share_resource_with_user(request, frm, res, user, PrivilegeCodes.VIEW)
    elif t == 'add_edit_user':
        frm = AddUserForm(data=request.POST)
        _share_resource_with_user(request, frm, res, user, PrivilegeCodes.CHANGE)
    # elif t == 'add_view_group':
    #     frm = AddGroupForm(data=request.POST)
    #     if frm.is_valid():
    #         res.view_groups.add(frm.cleaned_data['group'])
    # elif t == 'add_view_group':
    #     frm = AddGroupForm(data=request.POST)
    #     if frm.is_valid():
    #         res.edit_groups.add(frm.cleaned_data['group'])
    elif t == 'add_owner':
        frm = AddUserForm(data=request.POST)
        _share_resource_with_user(request, frm, res, user, PrivilegeCodes.OWNER)
    elif t == 'make_public':
        _set_resource_sharing_status(request, user, res, is_public=True)
    elif t == 'make_private' or t == 'make_not_discoverable':
        _set_resource_sharing_status(request, user, res, is_public=False)
    elif t == 'make_discoverable':
        _set_resource_sharing_status(request, user, res, is_public=False, is_discoverable=True)

    # due to self unsharing of a private resource the user will have no access to that resource
    # so need to redirect to the resource listing page
    if go_to_resource_listing_page:
        return HttpResponseRedirect('/my-resources/')
    else:
        return HttpResponseRedirect(request.META['HTTP_REFERER'])


# Needed for new access control UI functionality being developed by Mauriel
def share_resource_with_user(request, shortkey, privilege, user_id, *args, **kwargs):
    res, _, user = authorize(request, shortkey, edit=True, full=True, superuser=True)
    user_to_share_with = utils.user_from_id(user_id)
    status = 'success'
    err_message = ''
    if privilege == 'view':
        access_privilege = PrivilegeCodes.VIEW
    elif privilege == 'edit':
        access_privilege = PrivilegeCodes.CHANGE
    elif privilege == 'owner':
        access_privilege = PrivilegeCodes.OWNER
    else:
        err_message = "Not a valid privilege"
        access_privilege = PrivilegeCodes.NONE

    if access_privilege != PrivilegeCodes.NONE:
        try:
            user.uaccess.share_resource_with_user(res, user_to_share_with, access_privilege)
        except HSAccessException as exp:
            status = 'error'
            err_message = exp.message
    else:
        status = 'error'

    current_user_privilege = res.raccess.get_combined_privilege(user)
    if current_user_privilege == PrivilegeCodes.VIEW:
        current_user_privilege = "view"
    elif current_user_privilege == PrivilegeCodes.CHANGE:
        current_user_privilege = "change"
    elif current_user_privilege == PrivilegeCodes.OWNER:
        current_user_privilege = "owner"

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
    return HttpResponse(json.dumps(ajax_response_data))


# Needed for new access control UI functionality being developed by Mauriel
def unshare_resource_with_user(request, shortkey, user_id, *args, **kwargs):
    res, _, user = authorize(request, shortkey, edit=True, full=True, superuser=True)
    user_to_unshare_with = utils.user_from_id(user_id)

    try:
        if user.uaccess.can_unshare_resource_with_user(res, user_to_unshare_with):
            # requesting user is the resource owner or user is self unsharing (user is user_to_unshare_with)
            user.uaccess.unshare_resource_with_user(res, user_to_unshare_with)
        else:
            # requesting user is the original grantor of privilege to user_to_unshare_with
            user.uaccess.undo_share_resource_with_user(res, user_to_unshare_with)

        messages.success(request, "Resource unsharing was successful")
        if user == user_to_unshare_with and not res.raccess.public:
            # user has no access to the resource - redirect to resource listing page
            return HttpResponseRedirect('/my-resources/')
    except HSAccessException as exp:
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


@processor_for('my-resources')
@login_required
def my_resources(request, page):
    # import sys
    # sys.path.append("/home/docker/pycharm-debug")
    # import pydevd
    # pydevd.settrace('10.0.0.7', port=21000, suspend=False)
    user = request.user
    # get a list of resources with effective OWNER privilege
    owned_resources = user.uaccess.get_resources_with_explicit_access(PrivilegeCodes.OWNER)
    # get a list of resources with effective CHANGE privilege
    editable_resources = user.uaccess.get_resources_with_explicit_access(PrivilegeCodes.CHANGE)
    # get a list of resources with effective VIEW privilege
    viewable_resources = user.uaccess.get_resources_with_explicit_access(PrivilegeCodes.VIEW)

    owned_resources = list(owned_resources)
    editable_resources = list(editable_resources)
    viewable_resources = list(viewable_resources)
    favorite_resources = list(user.ulabels.favorited_resources)
    labeled_resources = list(user.ulabels.labeled_resources)
    discovered_resources = list(user.ulabels.my_resources)

    for res in owned_resources:
        res.owned = True

    for res in editable_resources:
        res.editable = True

    for res in viewable_resources:
        res.viewable = True

    for res in (owned_resources + editable_resources + viewable_resources + discovered_resources):
        res.is_favorite = False
        if res in favorite_resources:
            res.is_favorite = True
        if res in labeled_resources:
            res.labels = res.rlabels.get_labels(user)

    resource_collection = (owned_resources + editable_resources + viewable_resources + discovered_resources)

    context = {'collection': resource_collection}
    return context


@processor_for(GenericResource)
def add_generic_context(request, page):

    class AddUserForm(forms.Form):
        user = forms.ModelChoiceField(User.objects.all(), widget=autocomplete_light.ChoiceWidget("UserAutocomplete"))

    class AddGroupForm(forms.Form):
        group = forms.ModelChoiceField(Group.objects.all(), widget=autocomplete_light.ChoiceWidget("GroupAutocomplete"))

    return {
        'add_owner_user_form': AddUserForm(),
        'add_view_user_form': AddUserForm(),
        'add_edit_user_form': AddUserForm(),
        'add_view_group_form': AddGroupForm(),
        'add_edit_group_form': AddGroupForm(),
    }


@login_required
def create_resource_select_resource_type(request, *args, **kwargs):
    return render_to_response('pages/create-resource.html', context_instance=RequestContext(request))


@login_required
def create_resource(request, *args, **kwargs):
    resource_type = request.POST['resource-type']
    res_title = request.POST['title']

    resource_files = request.FILES.getlist('files')

    irods_fnames = request.POST.get('irods_file_names')
    if irods_fnames:
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
        page_url_dict, res_title, metadata = hydroshare.utils.resource_pre_create_actions(resource_type=resource_type, files=resource_files,
                                                                    resource_title=res_title,
                                                                    page_redirect_url_key=url_key, **kwargs)
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


def _share_resource_with_user(request, frm, resource, requesting_user, privilege):
    if frm.is_valid():
        try:
            requesting_user.uaccess.share_resource_with_user(resource, frm.cleaned_data['user'], privilege)
        except HSAccessException as exp:
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
                    requesting_user.uaccess.undo_share_resource_with_user(resource, user)

                if requesting_user == user and not resource.raccess.public:
                    go_to_resource_listing_page = True
            except HSAccessException as exp:
                messages.error(request, exp.message)
                break
    return go_to_resource_listing_page


def _set_resource_sharing_status(request, user, resource, is_public, is_discoverable=False):
    if not user.uaccess.can_change_resource_flags(resource):
        messages.error(request, "You don't have permission to change resource sharing status")
        return

    has_files = False
    has_metadata = False
    can_resource_be_public_or_discoverable = False
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
        istorage = IrodsStorage()
        istorage.setAVU(resource.short_id, "isPublic", str(resource.raccess.public))


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