from __future__ import absolute_import
from collections import defaultdict
import json
import requests
import os

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group, User
from django.contrib.sites.models import Site
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

from hs_core import hydroshare
from hs_core.hydroshare import get_resource_list
from hs_core.hydroshare.utils import get_resource_by_shortkey, resource_modified, user_from_id
from .utils import authorize, upload_from_irods
from hs_core.models import ResourceFile, GenericResource, resource_processor, CoreMetaData

from . import resource_rest_api
from . import user_rest_api

from hs_core.hydroshare import utils
from . import utils as view_utils
from hs_core.hydroshare import file_size_limit_for_display
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
        request.session['file_validation_error'] = ex.message
        return HttpResponseRedirect(request.META['HTTP_REFERER'])

    try:
        hydroshare.utils.resource_file_add_process(resource=resource, files=res_files, user=request.user,
                                                   extract_metadata=extract_metadata)

    except (hydroshare.utils.ResourceFileValidationException, Exception) as ex:
        request.session['file_validation_error'] = ex.message

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
                    element = res.metadata.create_element(element_name, **element_data_dict)

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

    is_redirect = False
    for receiver, response in handler_response:
        if 'is_valid' in response:
            if response['is_valid']:
                element_data_dict = response['element_data_dict']
                res.metadata.update_element(element_name, element_id, **element_data_dict)
                if element_name == 'title':
                    res.title = res.metadata.title.value
                    res.save()
                    if res.public:
                        if not res.can_be_public:
                            res.public = False
                            res.save()
                            is_redirect = True

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
    res.edit_users = []
    res.edit_groups = []
    res.published_and_frozen = True
    res.doi = "to be assigned"
    res.save()
    resource_modified(res, request.user)
    return HttpResponseRedirect(request.META['HTTP_REFERER'])


def change_permissions(request, shortkey, *args, **kwargs):

    class AddUserForm(forms.Form):
        user = forms.ModelChoiceField(User.objects.all(), widget=autocomplete_light.ChoiceWidget("UserAutocomplete"))

    class AddGroupForm(forms.Form):
        group = forms.ModelChoiceField(Group.objects.all(), widget=autocomplete_light.ChoiceWidget("GroupAutocomplete"))


    res, _, _ = authorize(request, shortkey, edit=True, full=True, superuser=True)
    t = request.POST['t']
    values = [int(k) for k in request.POST.getlist('designees', [])]
    if t == 'owners':
        res.owners = User.objects.in_bulk(values)
    elif t == 'edit_users':
        res.edit_users = User.objects.in_bulk(values)
    elif t == 'edit_groups':
        res.edit_groups = Group.objects.in_bulk(values)
    elif t == 'view_users':
        res.view_users = User.objects.in_bulk(values)
    elif t == 'view_groups':
        res.view_groups = Group.objects.in_bulk(values)
    elif t == 'add_view_user':
        frm = AddUserForm(data=request.POST)
        if frm.is_valid():
            res.view_users.add(frm.cleaned_data['user'])
    elif t == 'add_edit_user':
        frm = AddUserForm(data=request.POST)
        if frm.is_valid():
            res.edit_users.add(frm.cleaned_data['user'])
    elif t == 'add_view_group':
        frm = AddGroupForm(data=request.POST)
        if frm.is_valid():
            res.view_groups.add(frm.cleaned_data['group'])
    elif t == 'add_view_group':
        frm = AddGroupForm(data=request.POST)
        if frm.is_valid():
            res.edit_groups.add(frm.cleaned_data['group'])
    elif t == 'add_owner':
        frm = AddUserForm(data=request.POST)
        if frm.is_valid():
            res.owners.add(frm.cleaned_data['user'])
    elif t == 'make_public':
        #if res.metadata.has_all_required_elements():
        if res.can_be_public:
            res.public = True
            res.save()
    elif t == 'make_private':
        res.public = False
        res.save()

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

class CaptchaVerifyForm(forms.Form):
    challenge = forms.CharField()
    response = forms.CharField()

def verify_captcha(request):
    f = CaptchaVerifyForm(request.POST)
    if f.is_valid():
        params = dict(f.cleaned_data)
        params['privatekey'] = getattr(settings, 'RECAPTCHA_PRIVATE_KEY', '6LdNC_USAAAAADNdzytMK2-qmDCzJcgybFkw8Z5x')
        params['remoteip'] = request.META['REMOTE_ADDR']
        # return HttpResponse('true', content_type='text/plain')
        resp = requests.post('http://www.google.com/recaptcha/api/verify', params=params)
        lines = resp.text.split('\n')
        if lines[0].startswith('false'):
            raise ex.PermissionDenied('captcha failed')
        else:
            return HttpResponse('true', content_type='text/plain')

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
def my_resources(request, page):
    import sys
    sys.path.append("/home/docker/pycharm-debug")
    import pydevd
    pydevd.settrace('172.17.42.1', port=21000, suspend=False)

    frm = FilterForm(data=request.REQUEST)
    if frm.is_valid():
        res_cnt = 20 # 20 is hardcoded for the number of resources to show on one page, which is also hardcoded in my-resources.html
        owner = frm.cleaned_data['owner'] or None
        user = frm.cleaned_data['user'] or (request.user if request.user.is_authenticated() else None)
        edit_permission = frm.cleaned_data['edit_permission'] or False
        published = frm.cleaned_data['published'] or False
        startno = frm.cleaned_data['start']
        if(startno < 0):
            startno = 0
        start = startno or 0
        from_date = frm.cleaned_data['from_date'] or None
        words = request.REQUEST.get('text', None)
        public = not request.user.is_authenticated()

        search_items = dict(
            (item_type, [t.strip() for t in request.REQUEST.getlist(item_type)])
            for item_type in ("type", "author", "contributor", "subject")
        )

        # TODO ten separate SQL queries for basically the same data
        res = set()
        for lst in get_resource_list(
            user=user,
            owner= owner,
            published=published,
            edit_permission=edit_permission,
            from_date=from_date,
            full_text_search=words,
            public=public,
            **search_items
        ).values():
            res = res.union(lst)
        total_res_cnt = len(res)

        reslst = list(res)

        # need to return total number of resources as 'ct' so have to get all resources
        # and then filter by start and count
        # TODO this is doing some pagination/limits before sorting, so it won't be consistent
        if(start>=total_res_cnt):
            start = total_res_cnt-res_cnt
        if(start < 0):
            start = 0
        if(start+res_cnt > total_res_cnt):
            res_cnt = total_res_cnt-start

        reslst = reslst[start:start+res_cnt]

        # TODO sorts should be in SQL not python
        res = sorted(reslst, key=lambda x: x.title)

        return {
            'resources': res,
            'first': start,
            'last': start+len(res),
            'ct': total_res_cnt,
        }

@processor_for(GenericResource)
def add_generic_context(request, page):

    class AddUserForm(forms.Form):
        user = forms.ModelChoiceField(User.objects.all(), widget=autocomplete_light.ChoiceWidget("UserAutocomplete"))

    class AddGroupForm(forms.Form):
        group = forms.ModelChoiceField(Group.objects.all(), widget=autocomplete_light.ChoiceWidget("GroupAutocomplete"))

    cm = page.get_content_model()

    return {
        'resource_type': cm._meta.verbose_name,
        'bag': cm.bags.first(),
        'users': User.objects.all(),
        'groups': Group.objects.all(),
        'owners': set(cm.owners.all()),
        'view_users': set(cm.view_users.all()),
        'view_groups': set(cm.view_groups.all()),
        'edit_users': set(cm.edit_users.all()),
        'edit_groups': set(cm.edit_groups.all()),
        'add_owner_user_form': AddUserForm(),
        'add_view_user_form': AddUserForm(),
        'add_edit_user_form': AddUserForm(),
        'add_view_group_form': AddGroupForm(),
        'add_edit_group_form': AddGroupForm(),
    }

res_cls = ""
resource = None

@login_required
def create_resource_select_resource_type(request, *args, **kwargs):
    return render_to_response('pages/create-resource.html', context_instance=RequestContext(request))

@login_required
def create_resource(request, *args, **kwargs):
    resource_type = request.POST['resource-type']
    res_title = request.POST['title']

    resource_files = request.FILES.getlist('files')

    irods_fname = request.POST.get('irods_file_name')
    if irods_fname:
        user = request.POST.get('irods-username')
        password = request.POST.get("irods-password")
        port = request.POST.get("irods-port")
        host = request.POST.get("irods-host")
        zone = request.POST.get("irods-zone")
        try:
            upload_from_irods(username=user, password=password, host=host, port=port,
                                  zone=zone, irods_fname=irods_fname, res_files=resource_files)
        except Exception as ex:
            context = {'resource_creation_error': ex.message}
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
        context = {'file_validation_error': ex.message}
        return render_to_response('pages/create-resource.html', context, context_instance=RequestContext(request))

    except Exception as ex:
        context = {'resource_creation_error': ex.message}
        return render_to_response('pages/create-resource.html', context, context_instance=RequestContext(request))

    if url_key in page_url_dict:
        return render(request, page_url_dict[url_key], {'title': res_title, 'metadata': metadata})

    try:
        resource = hydroshare.create_resource(
                resource_type=request.POST['resource-type'],
                owner=request.user,
                title=res_title,
                keywords=None,
                metadata=metadata,
                files=resource_files,
                content=res_title
        )
    except Exception as ex:
        context = {'resource_creation_error': ex.message }
        return render_to_response('pages/create-resource.html', context, context_instance=RequestContext(request))

    try:
        utils.resource_post_create_actions(resource=resource, user=request.user, metadata=metadata, **kwargs)
    except (utils.ResourceFileValidationException, Exception) as ex:
        request.session['file_validation_error'] = ex.message

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

@processor_for('resources')
def resource_listing_processor(request, page):
    owned_resources = list(GenericResource.objects.filter(owners__pk=request.user.pk))
    editable_resources = list(GenericResource.objects.filter(owners__pk=request.user.pk))
    viewable_resources = list(GenericResource.objects.filter(public=True))
    return locals()

# FIXME need a task somewhere that amounts to checking inactive accounts and deleting them after 30 days.
