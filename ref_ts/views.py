from __future__ import absolute_import
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.utils.timezone import now
from django import forms
from django.http import HttpResponseRedirect
from mezzanine.pages.page_processors import processor_for
from ga_resources.utils import json_or_jsonp
from hs_core import hydroshare
from hs_core.hydroshare.hs_bagit import create_bag
from hs_core.models import ResourceFile
from . import ts_utils
from .models import RefTimeSeries
import requests
from lxml import etree
import datetime
from django.utils.timezone import now
import os

class ReferencedSitesForm(forms.Form):
    wsdl_url = forms.URLField()

def search_sites(request):
    f = ReferencedSitesForm(request.GET)
    if f.is_valid():
        params = f.cleaned_data
        url = params['wsdl_url']
        sites = ts_utils.sites_from_soap(url)

        return json_or_jsonp(request, sites)

class ReferencedVariablesForm(forms.Form):
    wsdl_url = forms.URLField()
    site = forms.CharField(min_length=0)

def search_variables(request):
    f = ReferencedVariablesForm(request.GET)
    if f.is_valid():
        params = f.cleaned_data
        url = params['wsdl_url']
        site = params['site']
        variables = ts_utils.site_info_from_soap(url, site=site)

        return json_or_jsonp(request, variables)


class GetTSValuesForm(forms.Form):
    ref_type = forms.CharField(min_length=0, required=True)
    service_url = forms.CharField(min_length=0, required=True)
    site = forms.CharField(min_length=0, required=False)
    variable = forms.CharField(min_length=0, required=False)

def time_series_from_service(request):
    f = GetTSValuesForm(request.GET)
    if f.is_valid():
        params = f.cleaned_data
        ref_type = params['ref_type']
        url = params['service_url']
        site = params.get('site')
        variable = params.get('variable')
        if ref_type == 'rest':
            ts = ts_utils.time_series_from_service(url, ref_type)
        else:
            ts = ts_utils.time_series_from_service(url, ref_type, site_name_or_code=site, variable_code=variable)
        return json_or_jsonp(request, ts)


class VerifyRestUrlForm(forms.Form):
    rest_url = forms.URLField()

def verify_rest_url(request):
    f = VerifyRestUrlForm(request.GET)
    if f.is_valid():
        params = f.cleaned_data
        url = params['rest_url']
        try:
            ts = requests.get(url)
            ts_xml = etree.XML(ts.text.encode('utf-8'))
            if 'timeSeriesResponse' in ts_xml.tag:
                return json_or_jsonp(request, ts.status_code)
            elif 'Collection' in ts_xml.tag:
                return json_or_jsonp(request, ts.status_code)
            else:
                return json_or_jsonp(request, 400)
        except:
            return json_or_jsonp(request, 400)

class CreateRefTimeSeriesForm(forms.Form):
    title = forms.CharField(required=True)
    creators = forms.CharField(required=False, min_length=0)
    contributors = forms.CharField(required=False, min_length=0)
    abstract = forms.CharField(required=False, min_length=0)
    keywords = forms.CharField(required=False, min_length=0)
    rest_url = forms.URLField(required=False)
    wsdl_url = forms.URLField(required=False)
    reference_type = forms.CharField(required=False, min_length=0)
    site = forms.CharField(required=False, min_length=0)
    variable = forms.CharField(required=False, min_length=0)
    start_date = forms.CharField(required=True, min_length=0)

@login_required
def create_ref_time_series(request, *args, **kwargs):
    frm = CreateRefTimeSeriesForm(request.POST)
    if frm.is_valid():
        dcterms = [
            { 'term': 'T', 'content': frm.cleaned_data['title']},
            { 'term': 'AB', 'content': frm.cleaned_data['abstract'] or frm.cleaned_data['title']},
            { 'term': 'DTS', 'content': now().isoformat()}
        ]
        for cn in frm.cleaned_data['contributors'].split(','):
            cn = cn.strip()
            dcterms.append({'term' : 'CN', 'content' : cn})
        for cr in frm.cleaned_data['creators'].split(','):
            cr = cr.strip()
            dcterms.append({'term' : 'CR', 'content' : cr})

        if frm.cleaned_data['wsdl_url']:
            url = frm.cleaned_data['wsdl_url']
        elif frm.cleaned_data['rest_url']:
            url = frm.cleaned_data['rest_url']
        else:
            url = ''

        start_date_str = frm.cleaned_data["start_date"]
        start_date_int = ts_utils.time_to_int(start_date_str)
        start_date = datetime.datetime.fromtimestamp(start_date_int)
        site_name, site_code, variable_name, variable_code = None, None, None, None

        if frm.cleaned_data.get('site'):
            full_site = frm.cleaned_data['site'].replace(' ', '')
            n = full_site.index(':')
            site_name = full_site[:n]
            site_code = full_site[n+1:]

        if frm.cleaned_data.get('variable'):
            full_variable = frm.cleaned_data['variable'].replace(' ', '')
            n = full_variable.index(':')
            variable_name = full_variable[:n]
            variable_code = full_variable[n+1:]
        reference_type = frm.cleaned_data['reference_type']
        title = frm.cleaned_data['title']

        res = hydroshare.create_resource(
            resource_type='RefTimeSeries',
            owner=request.user,
            title=title,
            keywords=[k.strip() for k in frm.cleaned_data['keywords'].split(',')] if frm.cleaned_data['keywords'] else None,
            dublin_metadata=dcterms,
            content=frm.cleaned_data['abstract'] or frm.cleaned_data['title'],
            reference_type=reference_type,
            url=url,
            data_site_name=site_name,
            data_site_code=site_code,
            variable_name=variable_name,
            variable_code=variable_code,
            start_date=start_date,
            end_date=now(),
        )
        ts_utils.generate_files(res.short_id)
        return HttpResponseRedirect(res.get_absolute_url())

@processor_for(RefTimeSeries)
def add_dublin_core(request, page):
    from dublincore import models as dc

    class DCTerm(forms.ModelForm):
        class Meta:
            model = dc.QualifiedDublinCoreElement
            fields = ['term', 'content']

    cm = page.get_content_model()
    resfiles = []
    visfile = ''
    for f in cm.files.all():
        if 'visual' in str(f.resource_file.name):
            visfile = f
        elif f.resource_file:
            resfiles.append(f)
        else:
            f.delete()

    try:
        abstract = cm.dublin_metadata.filter(term='AB').first().content
    except:
        abstract = None

    return {
        'dublin_core': [t for t in cm.dublin_metadata.all().exclude(term='AB').exclude(term='DM').exclude(term='DC').exclude(term='DTS').exclude(term='T')],
        'abstract' : abstract,
        'short_id' : cm.short_id,
        'resource_type': cm._meta.verbose_name,
        'reference_type': cm.reference_type,
        'url': cm.url,
        'site_name': cm.data_site_name if cm.data_site_name else '',
        'site_code' : cm.data_site_code if cm.data_site_code else '',
        'variable_name': cm.variable_name if cm.variable_name else '',
        'variable_code': cm.variable_code if cm.variable_code else '',
        'visfile':visfile,
        'resfiles': resfiles,
        'files': cm.files.all(),
        'dcterm_frm': DCTerm(),
        'bag': cm.bags.first(),
        'first_4_bags': cm.bags.all()[:4],
        'users': User.objects.all(),
        'groups': Group.objects.all(),
        'owners': set(cm.owners.all()),
        'view_users': set(cm.view_users.all()),
        'view_groups': set(cm.view_groups.all()),
        'edit_users': set(cm.edit_users.all()),
        'edit_groups': set(cm.edit_groups.all()),
    }



def update_files(request, shortkey, *args, **kwargs):

    res = hydroshare.get_resource_by_shortkey(shortkey)

    files = ts_utils.make_files(res.reference_type, res.url, res.data_site_code, res.variable_code, res.title)
    if files:
        if len(res.files.all())>0:
            for f in res.files.all():
                f.resource_file.delete()
        res_files = []
        for f in files:
            res_file = hydroshare.add_resource_files(res.short_id, f)[0]
            res_files.append(res_file)
            os.remove(f.name)
        for fl in res.files.all():
            if fl.resource_file:
                pass
            else:
                fl.delete()

        # cap 3 bags per day, 5 overall
        bag = ''
        bag = create_bag(res)
        if len(res.bags.all()) > 5:
            for b in res.bags.all()[5:]:
                b.delete()
        for f in res_files:
            if str(f.resource_file).endswith('.csv'):
                csv_name = str(f.resource_file)
                sl_loc = csv_name.rfind('/')
                csv_name = csv_name[sl_loc+1:]
                csv_link = f.resource_file.url
                csv_size = f.resource_file.size
            if str(f.resource_file).endswith('.xml') and 'wml_2' in str(f.resource_file):
                wml2_name = str(f.resource_file)
                sl_loc = wml2_name.rfind('/')
                wml2_name = wml2_name[sl_loc+1:]
                wml2_link = f.resource_file.url
                wml2_size = f.resource_file.size
            if str(f.resource_file).endswith('.xml') and 'wml_1' in str(f.resource_file):
                wml1_name = str(f.resource_file)
                sl_loc = wml1_name.rfind('/')
                wml1_name = wml1_name[sl_loc+1:]
                wml1_link = f.resource_file.url
                wml1_size = f.resource_file.size
            if 'visual' in str(f.resource_file):
                vis_link = f.resource_file.url

        status_code = 200

        #changing date to match Django formatting
        time = bag.timestamp.date().strftime('%b. %d, %Y, %I:%M %P')
        if time.endswith('am'):
            time = time[:-2]+'a.m.'
        elif time.endswith('pm'):
            time = time[:-2]+'p.m.'

        data = {'status_code': status_code,
                'csv_name': csv_name,
                'csv_link': csv_link,
                'csv_size': csv_size,
                'wml1_name': wml1_name,
                'wml1_link': wml1_link,
                'wml1_size': wml1_size,
                'wml2_name': wml2_name,
                'wml2_link': wml2_link,
                'wml2_size': wml2_size,
                'vis_link': vis_link,
                'bag_url': bag.bag.url,
                'bag_time': time
        }
        return json_or_jsonp(request, data)  # successfully generated new files
