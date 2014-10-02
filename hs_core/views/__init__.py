from __future__ import absolute_import
from collections import defaultdict
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group, User
from django.contrib.sites.models import Site
from django.core.exceptions import ValidationError
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.utils.timezone import now
from mezzanine.conf import settings
from django import forms
from mezzanine.generic.models import Keyword
from hs_core import hydroshare
from hs_core.hydroshare import get_resource_list
from hs_core.hydroshare.utils import get_resource_by_shortkey, resource_modified
from .utils import authorize
from hs_core.models import ResourceFile, GenericResource
import requests
from django.core import exceptions as ex
from mezzanine.pages.page_processors import processor_for

from . import users_api
from . import discovery_api
from . import resource_api
from . import social_api

import autocomplete_light


def short_url(request, *args, **kwargs):
    try:
        shortkey = kwargs['shortkey']
    except KeyError:
        raise TypeError('shortkey must be specified...')

    m = get_resource_by_shortkey(shortkey)
    return HttpResponseRedirect(m.get_absolute_url())

def verify(request, *args, **kwargs):
    uid = int(kwargs['pk'])
    u = User.objects.get(pk=uid)
    if not u.is_active:
        u.is_active=True
        u.save()
        u.groups.add(Group.objects.get(name="Hydroshare Author"))
        return HttpResponseRedirect('/account/update/')


def add_file_to_resource(request, *args, **kwargs):
    try:
        shortkey = kwargs['shortkey']
    except KeyError:
        raise TypeError('shortkey must be specified...')

    res, _, _ = authorize(request, shortkey, edit=True, full=True, superuser=True)
    for f in request.FILES.getlist('files'):
        res.files.add(ResourceFile(content_object=res, resource_file=f))
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


def delete_file(request, shortkey, f, *args, **kwargs):
    res, _, _ = authorize(request, shortkey, edit=True, full=True, superuser=True)
    fl = res.files.filter(pk=int(f)).first()
    fl.resource_file.delete()
    fl.delete()
    resource_modified(res, request.user)
    return HttpResponseRedirect(request.META['HTTP_REFERER'])


def delete_resource(request, shortkey, *args, **kwargs):
    res, _, _ = authorize(request, shortkey, edit=True, full=True, superuser=True)
    for fl in res.files.all():
        fl.resource_file.delete()
    for bag in res.bags.all():
        bag.bag.delete()
        bag.delete()
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
        res.public = True
        res.save()
    elif t == 'make_private':
        res.public = False
        res.save()

    return HttpResponseRedirect(request.META['HTTP_REFERER'])



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

    frm = FilterForm(data=request.REQUEST)
    if frm.is_valid():
        owner = frm.cleaned_data['creator'] or None
        user = frm.cleaned_data['user'] or (request.user if request.user.is_authenticated() else None)
        edit_permission = frm.cleaned_data['edit_permission'] or False
        published = frm.cleaned_data['published'] or False
        start = frm.cleaned_data['start'] or 0
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
            count=20,
            published=published,
            edit_permission=edit_permission,
            start=start,
            from_date=from_date,
            dc=list(dcterms.values()) if dcterms else None,
            keywords=keywords if keywords else None,
            public=public
        ).values():
            res = res.union(lst)

        res = sorted(list(res), key=lambda x: x.title)
        return {
            'resources': res,
            'first': start,
            'last': start+len(res),
            'ct': len(res),
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


class CreateResourceForm(forms.Form):
    title = forms.CharField(required=True)
    creators = forms.CharField(required=False, min_length=0)
    contributors = forms.CharField(required=False, min_length=0)
    abstract = forms.CharField(required=False, min_length=0)
    keywords = forms.CharField(required=False, min_length=0)

@login_required
def create_resource(request, *args, **kwargs):
    frm = CreateResourceForm(request.POST)
    if frm.is_valid():
        dcterms = [
            { 'term': 'T', 'content': frm.cleaned_data['title'] },
            { 'term': 'AB',  'content': frm.cleaned_data['abstract'] or frm.cleaned_data['title']},
            { 'term': 'DT', 'content': now().isoformat()},
            { 'term': 'DC', 'content': now().isoformat()}
        ]
        for cn in frm.cleaned_data['contributors'].split(','):
            cn = cn.strip()
            dcterms.append({'term': 'CN', 'content': cn})
        for cr in frm.cleaned_data['creators'].split(','):
            cr = cr.strip()
            dcterms.append({'term': 'CR', 'content': cr})

        res = hydroshare.create_resource(
            resource_type=request.POST['resource-type'],
            owner=request.user,
            title=frm.cleaned_data['title'],
            keywords=[k.strip() for k in frm.cleaned_data['keywords'].split(',')] if frm.cleaned_data['keywords'] else None, 
            dublin_metadata=dcterms,
            files=request.FILES.getlist('files'),
            content=frm.cleaned_data['abstract'] or frm.cleaned_data['title']
        )
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


# FIXME need a task somewhere that amounts to checking inactive accounts and deleting them after 30 days.
