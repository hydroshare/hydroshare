from __future__ import absolute_import
from collections import defaultdict
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group, User
from django.contrib.sites.models import Site
from django.core.exceptions import ValidationError
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import get_object_or_404, render_to_response, render
from django.template import RequestContext
from django.utils.timezone import now
import json
from mezzanine.conf import settings
from django import forms
from mezzanine.generic.models import Keyword
import mimetypes
import os
from hs_core import hydroshare
from hs_core.hydroshare import get_resource_list
from hs_core.hydroshare.utils import get_resource_by_shortkey, resource_modified, user_from_id
from .utils import authorize
from hs_core.models import ResourceFile, GenericResource, resource_processor, CoreMetaData
import requests
from django.core import exceptions as ex
from mezzanine.pages.page_processors import processor_for
from django.template import RequestContext
from django.core import signing
from django.template import Context
import django.dispatch
from django.contrib.contenttypes.models import ContentType
from django.forms import ValidationError
from inplaceeditform.commons import get_dict_from_obj, apply_filters, get_adaptor_class
from inplaceeditform.views import _get_http_response, _get_adaptor

from . import users_api
from . import discovery_api
from . import resource_api
from . import social_api
from hs_core.hydroshare import utils
from hs_core.hydroshare import file_size_limit_for_display
from hs_core.signals import *
import autocomplete_light

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


def add_file_to_resource(request, *args, **kwargs):
    try:
        shortkey = kwargs['shortkey']
    except KeyError:
        raise TypeError('shortkey must be specified...')

    res, _, _ = authorize(request, shortkey, edit=True, full=True, superuser=True)

    res_files = request.FILES.getlist('files')
    for f in res_files:
        res.files.add(ResourceFile(content_object=res, resource_file=f))

        # add format metadata element if necessary
        file_format_type = utils.get_file_mime_type(f.name)
        if file_format_type not in [mime.value for mime in res.metadata.formats.all()]:
            res.metadata.create_element('format', value=file_format_type)
    pre_add_files_to_resource.send(sender=res_cls, files=res_files, resource=res, **kwargs)
    resource_modified(res, request.user)
    return HttpResponseRedirect(request.META['HTTP_REFERER'])

def add_citation(request, shortkey, *args, **kwargs):
    res, _, _ = authorize(request, shortkey, edit=True, full=True, superuser=True)
    res.dublin_metadata.create(term='REF', content=request.REQUEST['content'])
    resource_modified(res, request.user)
    return HttpResponseRedirect(request.META['HTTP_REFERER'])


def add_metadata_term(request, shortkey, *args, **kwargs):
    res, _, _ = authorize(request, shortkey, edit=True, full=True, superuser=True)
    res.dublin_metadata.create(
        term=request.REQUEST['term'],
        content=request.REQUEST['content']
    )
    resource_modified(res, request.user)
    return HttpResponseRedirect(request.META['HTTP_REFERER'])


def _get_resource_sender(element_name, resource):
    core_metadata_element_names = [el_name.lower() for el_name in CoreMetaData.get_supported_element_names()]

    if element_name in core_metadata_element_names:
        sender_resource = GenericResource().__class__
    else:
        sender_resource = resource.__class__

    return sender_resource


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


def delete_metadata_element(request, shortkey, element_name, element_id, *args, **kwargs):
    res, _, _ = authorize(request, shortkey, edit=True, full=True, superuser=True)
    res.metadata.delete_element(element_name, element_id)
    resource_modified(res, request.user)
    request.session['resource-mode'] = 'edit'
    return HttpResponseRedirect(request.META['HTTP_REFERER'])


def delete_file(request, shortkey, f, *args, **kwargs):
    res, _, _ = authorize(request, shortkey, edit=True, full=True, superuser=True)
    fl = res.files.filter(pk=int(f)).first()
    file_name = fl.resource_file.name
    pre_delete_file_from_resource.send(sender=res_cls, file=fl, resource=res, **kwargs)
    fl.resource_file.delete()
    fl.delete()

    delete_file_mime_type = utils.get_file_mime_type(file_name)
    delete_file_extension = os.path.splitext(file_name)[1]
    # if there is no other resource file with the same extension as the
    # file just deleted then delete the matching format metadata element for the resource
    resource_file_extensions = [os.path.splitext(f.resource_file.name)[1] for f in res.files.all()]
    if delete_file_extension not in resource_file_extensions:
        format_element = res.metadata.formats.filter(value=delete_file_mime_type).first()

        res.metadata.delete_element(format_element.term, format_element.id)

    if res.public:
        if not res.can_be_public:
            res.public = False
            res.save()

    resource_modified(res, request.user)
    return HttpResponseRedirect(request.META['HTTP_REFERER'])


def delete_resource(request, shortkey, *args, **kwargs):
    res, _, _ = authorize(request, shortkey, edit=True, full=True, superuser=True)

    for fl in res.files.all():
        fl.resource_file.delete()

    for bag in res.bags.all():
        bag.bag.delete()
        bag.delete()

    res.metadata.delete_all_elements()
    res.metadata.delete()
    # deleting the metadata container object deletes the resource
    # so no need to delete the resource separately
    #res.delete()
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

@processor_for('resend-verification-email')
def resend_verification_email(request, page):
    u = get_object_or_404(User, username=request.GET['user'])
    try:
        u.email_user(
            'Please verify your new Hydroshare account.',
            """
This is an automated email from Hydroshare.org. If you requested a Hydroshare account, please
go to http://{domain}/verify/{uid}/ and verify your account.
""".format(
            domain=Site.objects.get_current().domain,
            uid=u.pk
        ))
    except:
        pass # FIXME should log this instead of ignoring it.


class FilterForm(forms.Form):
    start = forms.IntegerField(required=False)
    published = forms.BooleanField(required=False)
    edit_permission = forms.BooleanField(required=False)
    creator = forms.ModelChoiceField(queryset=User.objects.all(), required=False)
    user = forms.ModelChoiceField(queryset=User.objects.all(), required=False)
    from_date = forms.DateTimeField(required=False)



@processor_for('my-resources')
def my_resources(request, page):
#    if not request.user.is_authenticated():
#        return HttpResponseRedirect('/accounts/login/')

    # TODO: remove the following 4 lines of debugging code prior to pull request
    # import sys
    # sys.path.append("/home/docker/pycharm-debug")
    # import pydevd
    # pydevd.settrace('172.17.42.1', port=21000, suspend=False)

    # from hs_core.hydroshare import users
    # users.create_account(email="hong.yi.hello@gmail.com", username="test1", first_name="Hong", last_name="Yi", password="test123")

    frm = FilterForm(data=request.REQUEST)
    if frm.is_valid():
        res_cnt = 20 # 20 is hardcoded for the number of resources to show on one page, which is also hardcoded in my-resources.html
        owner = frm.cleaned_data['creator'] or None
        user = frm.cleaned_data['user'] or (request.user if request.user.is_authenticated() else None)
        edit_permission = frm.cleaned_data['edit_permission'] or False
        published = frm.cleaned_data['published'] or False
        startno = frm.cleaned_data['start']
        if(startno < 0):
            startno = 0
        start = startno or 0
        from_date = frm.cleaned_data['from_date'] or None
        keywords = [k.strip() for k in request.REQUEST['keywords'].split(',')] if request.REQUEST.get('keywords', None) else None
        public = not request.user.is_authenticated()

        dcterms = defaultdict(dict)
        for k, v in filter(lambda (x, y): x.startswith('dc'), request.REQUEST.items()):
            num = int(k[-1])
            vtype = k[2:-1]
            dcterms[num][vtype] = v

        res = set()
        for lst in get_resource_list(
            user=user,
            owner= owner,
            published=published,
            edit_permission=edit_permission,
            from_date=from_date,
            dc=list(dcterms.values()) if dcterms else None,
            keywords=keywords if keywords else None,
            public=public
        ).values():
            res = res.union(lst)
        total_res_cnt = len(res)

        reslst = list(res)

        # need to return total number of resources as 'ct' so have to get all resources
        # and then filter by start and count
        if(start>=total_res_cnt):
            start = total_res_cnt-res_cnt
        if(start < 0):
            start = 0
        if(start+res_cnt > total_res_cnt):
            res_cnt = total_res_cnt-start

        reslst = reslst[start:start+res_cnt]

        res = sorted(reslst, key=lambda x: x.title)

        return {
            'resources': res,
            'first': start,
            'last': start+len(res),
            'ct': total_res_cnt,
            'dcterms' : (
                ('AB', 'Abstract'),
                ('BX', 'Box'),
                ('CN', 'Contributor'),
                ('CVR', 'Coverage'),
                ('CR', 'Creator'),
                ('DT', 'Date'),
                ('DTS', 'DateSubmitted'),
                ('DC', 'DateCreated'),
                ('DM', 'DateModified'),
                ('DSC', 'Description'),
                ('FMT', 'Format'),
                ('ID', 'Identifier'),
                ('LG', 'Language'),
                ('PD', 'Period'),
                ('PT', 'Point'),
                ('PBL', 'Publisher'),
                ('REL', 'Relation'),
                ('RT', 'Rights'),
                ('SRC', 'Source'),
                ('SUB', 'Subject'),
                ('T', 'Title'),
                ('TYP', 'Type'),
    )
        }

@processor_for(GenericResource)
def add_dublin_core(request, page):

    class AddUserForm(forms.Form):
        user = forms.ModelChoiceField(User.objects.all(), widget=autocomplete_light.ChoiceWidget("UserAutocomplete"))

    class AddGroupForm(forms.Form):
        group = forms.ModelChoiceField(Group.objects.all(), widget=autocomplete_light.ChoiceWidget("GroupAutocomplete"))

    from dublincore import models as dc

    class DCTerm(forms.ModelForm):
        class Meta:
            model=dc.QualifiedDublinCoreElement
            fields = ['term', 'content']

    cm = page.get_content_model()
    try:
        abstract = cm.dublin_metadata.filter(term='AB').first().content
    except:
        abstract = None

    return {
        'dublin_core' : [t for t in cm.dublin_metadata.all().exclude(term='AB')],
        'abstract' : abstract,
        'resource_type' : cm._meta.verbose_name,
        'dcterm_frm' : DCTerm(),
        'bag' : cm.bags.first(),
        'users' : User.objects.all(),
        'groups' : Group.objects.all(),
        'owners' : set(cm.owners.all()),
        'view_users' : set(cm.view_users.all()),
        'view_groups' : set(cm.view_groups.all()),
        'edit_users' : set(cm.edit_users.all()),
        'edit_groups' : set(cm.edit_groups.all()),
        'add_owner_user_form' : AddUserForm(),
        'add_view_user_form' : AddUserForm(),
        'add_edit_user_form' : AddUserForm(),
        'add_view_group_form' : AddGroupForm(),
        'add_edit_group_form' : AddGroupForm(),
    }

res_cls = ""
resource = None
@login_required
def describe_resource(request, *args, **kwargs):
    resource_type=request.POST['resource-type']
    res_title = request.POST['title']
    global res_cls, resource
    resource_files=request.FILES.getlist('files')
    valid = hydroshare.check_resource_files(resource_files)
    if not valid:
        context = {
            'file_size_error' : 'The resource file is larger than the supported size limit %s. Select resource files within %s to create resource.' % (file_size_limit_for_display, file_size_limit_for_display)
        }
        return render_to_response('pages/resource-selection.html', context, context_instance=RequestContext(request))
    res_cls = hydroshare.check_resource_type(resource_type)
    # Send pre_describe_resource signal for other resource type apps to listen, extract, and add their own metadata
    ret_responses = pre_describe_resource.send(sender=res_cls, files=resource_files, title=res_title)

    create_res_context = {
        'resource_type': resource_type,
        'res_title': res_title,
    }
    page_url = 'pages/create-resource.html'
    use_generic = True
    for receiver, response in ret_responses:
        if response is not None:
            for key in response:
                if key != 'create_resource_page_url':
                    create_res_context[key] = response[key]
                else:
                    page_url = response.get('create_resource_page_url', 'pages/create-resource.html')
                    use_generic = False

    if use_generic:
        # create barebone resource with resource_files to database model for later update since on Django 1.7, resource_files get closed automatically at the end of each request
        owner = user_from_id(request.user)
        resource = res_cls.objects.create(
                user=owner,
                creator=owner,
                title=res_title,
                last_changed_by=owner,
                in_menus=[],
                **kwargs
        )
        for file in resource_files:
            ResourceFile.objects.create(content_object=resource, resource_file=file)

    return render_to_response(page_url, create_res_context, context_instance=RequestContext(request))


@login_required
def create_resource_select_resource_type(request, *args, **kwargs):
    return render_to_response('pages/create-resource.html', context_instance=RequestContext(request))


@login_required
def create_resource_new_workflow(request, *args, **kwargs):
    resource_type=request.POST['resource-type']
    res_title = request.POST['title']
    if len(res_title) == 0:
        res_title = 'Untitled resource'

    global res_cls, resource
    resource_files = request.FILES.getlist('files')
    valid = hydroshare.check_resource_files(resource_files)
    if not valid:
        context = {
            'file_size_error' : 'The resource file is larger than the supported size limit %s. '
                                'Select resource files within %s to create resource.'
                                % (file_size_limit_for_display, file_size_limit_for_display)
        }
        return render_to_response('pages/create-resource.html', context, context_instance=RequestContext(request))

    res_cls = hydroshare.check_resource_type(resource_type)

    metadata = []
    page_url_dict = {}
    url_key = "page_redirect_url"
    # Send pre-create resource signal - let any other app populate the empty metadata list object
    # also pass title to other apps, and give other apps a chance to populate page_redirect_url if they want
    # to redirect to their own page for resource creation rather than use core resource creation code
    pre_create_resource.send(sender=res_cls, dublin_metadata=None, metadata=metadata, files=resource_files, title=res_title, url_key=url_key, page_url_dict=page_url_dict, **kwargs)
    # redirect to a specific resource creation page if other apps choose so
    #if url_key in page_url_dict:
    #    return HttpResponseRedirect(page_url_dict[url_key])
            'resource_type': resource_type,
            'res_title': res_title,
        }
        return render_to_response(page_url_dict[url_key], create_res_context, context_instance=RequestContext(request))

    # generic resource core metadata and resource creation
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
                #language_code = element['language']['code']
                add_language = False
            else:
                metadata.remove(element)
            break

    if add_language:
        metadata.append({'language': {'code': 'eng'}})

    # add the default rights/license element
    metadata.append({'rights':
                         {'statement': 'This resource is shared under the Creative Commons Attribution CC BY.',
                          'url': 'http://creativecommons.org/licenses/by/4.0/'
                         }
                    })

    resource = hydroshare.create_resource(
            resource_type=request.POST['resource-type'],
            owner=request.user,
            title=res_title,
            keywords=None,
            dublin_metadata=None,
            metadata=metadata,
            files=request.FILES.getlist('files'),
            content=res_title
    )

    # Send post-create resource signal
    post_create_resource.send(sender=res_cls, resource=resource, metadata=metadata, **kwargs)
    if url_key in page_url_dict:
        return render(request, page_url_dict[url_key], {'resource': resource})

    if resource is not None:
        # go to resource landing page
        return HttpResponseRedirect(resource.get_absolute_url())
    else:
        context = {
            'resource_creation_error': 'Resource creation failed'
        }
        return render_to_response('pages/create-resource.html', context, context_instance=RequestContext(request))


class CreateResourceForm(forms.Form):
    title = forms.CharField(required=True)
    creators = forms.CharField(required=False, min_length=0)
    contributors = forms.CharField(required=False, min_length=0)
    abstract = forms.CharField(required=False, min_length=0)
    keywords = forms.CharField(required=False, min_length=0)

@login_required
def create_resource(request, *args, **kwargs):
    global resource
    qrylst = request.POST
    frm = CreateResourceForm(qrylst)
    if frm.is_valid():
        dcterms = [
            { 'term': 'T', 'content': frm.cleaned_data['title'] },
            { 'term': 'AB',  'content': frm.cleaned_data['abstract'] or frm.cleaned_data['title']},
            { 'term': 'DT', 'content': now().isoformat()},
            { 'term': 'DC', 'content': now().isoformat()}
        ]
        for cn in frm.cleaned_data['contributors'].split(','):
            cn = cn.strip()
            if(cn !=""):
                dcterms.append({'term': 'CN', 'content': cn})
        for cr in frm.cleaned_data['creators'].split(','):
            cr = cr.strip()
            if(cr !=""):
                dcterms.append({'term': 'CR', 'content': cr})
        global res_cls
        # Send pre_call_create_resource signal
        metadata = []
        pre_call_create_resource.send(sender=res_cls, resource=resource, metadata=metadata, request_post = qrylst)
        res = hydroshare.create_resource(
            resource_type=qrylst['resource-type'],
            owner=request.user,
            title=frm.cleaned_data['title'],
            keywords=[k.strip() for k in frm.cleaned_data['keywords'].split(',')] if frm.cleaned_data['keywords'] else None,
            dublin_metadata=dcterms,
            content=frm.cleaned_data['abstract'] or frm.cleaned_data['title'],
            res_type_cls = res_cls,
            resource=resource,
            metadata=metadata
        )
        if res is not None:
            return HttpResponseRedirect(res.get_absolute_url())
    else:
        raise ValidationError(frm.errors)

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
