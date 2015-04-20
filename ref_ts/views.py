from __future__ import absolute_import
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.utils.timezone import now
from django import forms
from django.http import HttpResponseRedirect, HttpResponseNotFound
from mezzanine.pages.page_processors import processor_for
from ga_resources.utils import json_or_jsonp
from hs_core import hydroshare, page_processors
from hs_core.hydroshare.hs_bagit import create_bag
from hs_core.models import ResourceFile
from . import ts_utils
from .models import RefTimeSeries
import requests
from lxml import etree
import datetime
from django.utils.timezone import now
import os
from hs_core.signals import post_create_resource
import ast

def get_his_urls(request):
    service_url = 'http://hiscentral.cuahsi.org/webservices/hiscentral.asmx/GetWaterOneFlowServiceInfo'
    r = requests.get(service_url)
    if r.status_code == 200:
        response = r.text.encode('utf-8')
        root = etree.XML(response)
    url_list = []
    for element in root.iter():
        if "servURL" in element.tag:
            url_list.append(element.text)
    return json_or_jsonp(request, url_list)


class ReferencedSitesForm(forms.Form):
    url = forms.URLField()

def search_sites(request):
    f = ReferencedSitesForm(request.GET)
    if f.is_valid():
        params = f.cleaned_data
        url = params['url']
        sites = ts_utils.sites_from_soap(url)

        return json_or_jsonp(request, sites)

class ReferencedVariablesForm(forms.Form):
    url = forms.URLField()
    site = forms.CharField(min_length=0)

def search_variables(request):
    f = ReferencedVariablesForm(request.GET)
    if f.is_valid():
        params = f.cleaned_data
        url = params['url']
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
            site = ts.get('site_code')
            variable = ts.get('variable_code')
        else:
            ts = ts_utils.time_series_from_service(url, ref_type, site_name_or_code=site, variable_code=variable)
        for_graph = ts['for_graph']
        units = ts['units']
        variable_name = ts['variable_name']
        noDataValue = ts.get('noDataValue', None)
        vis_file = ts_utils.create_vis("theme/static/img/", variable, site, for_graph, 'Date', variable_name, units, noDataValue)
        vis_file_name = os.path.basename(vis_file.name)
        return json_or_jsonp(request, {'vis_file_name': vis_file_name})


class VerifyRestUrlForm(forms.Form):
    url = forms.URLField()

def verify_rest_url(request):
    f = VerifyRestUrlForm(request.GET)
    if f.is_valid():
        params = f.cleaned_data
        url = params['url']
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
    url = forms.URLField(required=False)
    site = forms.CharField(required=False, min_length=0)
    variable = forms.CharField(required=False, min_length=0)
    metadata = forms.CharField(required=False, min_length=0)
    title = forms.CharField(required=False, min_length=0)

@login_required
def create_ref_time_series(request, *args, **kwargs):
    frm = CreateRefTimeSeriesForm(request.POST)
    if frm.is_valid():

        if frm.cleaned_data['url']:
            url = frm.cleaned_data['url']
        else:
            url = ''

        if url.endswith('WSDL') or url.endswith('wsdl'):
            reference_type = 'soap'
        else:
            reference_type = 'rest'
        reference_type = unicode(reference_type)

        # start_date_str = frm.cleaned_data["start_date"]
        # start_date_int = ts_utils.time_to_int(start_date_str)
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
        metadata = frm.cleaned_data.get('metadata')
        metadata = ast.literal_eval(metadata)
        res = hydroshare.create_resource(
            resource_type='RefTimeSeries',
            owner=request.user,
            title=frm.cleaned_data.get('title'),
            metadata=metadata
        )

        if reference_type == 'rest':
            ts = ts_utils.time_series_from_service(url, 'rest')
            site_code = ts['site_code']
            site_name = ts['site_name']
            variable_code = ts['variable_code']
            variable_name = ts['variable_name']
        else:
            ts = ts_utils.time_series_from_service(url, 'soap',
                                                   site_name_or_code=site_code,
                                                   variable_code=variable_code)

        hydroshare.resource.create_metadata_element(
            res.short_id,
            'QualityControlLevel',
            value=ts['QClevel'],
            )

        hydroshare.resource.create_metadata_element(
            res.short_id,
            'Method',
            value=ts['method'],
            )

        hydroshare.resource.create_metadata_element(
            res.short_id,
            'ReferenceURL',
            value=url,
            type=reference_type
        )

        hydroshare.resource.create_metadata_element(
            res.short_id,
            'Site',
            name=site_name,
            code=site_code,
            latitude=ts['latitude'],
            longitude=ts['longitude']
        )

        hydroshare.resource.create_metadata_element(
            res.short_id,
            'Variable',
            name=variable_name,
            code=variable_code,
            sample_medium=ts.get('sample_medium', 'unknown')
        )

        ts_utils.generate_files(res.short_id)

        for file_name in os.listdir("theme/static/img"):
            if 'visualization' in file_name:
                # open(file_name, 'w')
                os.remove("theme/static/img/"+file_name)

        return HttpResponseRedirect(res.get_absolute_url())

@processor_for(RefTimeSeries)
def add_dublin_core(request, page):
    content_model = page.get_content_model()
    edit_resource = page_processors.check_resource_mode(request)
    context = page_processors.get_page_context(page, request.user, resource_edit=edit_resource, extended_metadata_layout=None)
    extended_metadata_exists = False
    if content_model.metadata.sites.all().first() or \
            content_model.metadata.variables.all().first() or \
            content_model.metadata.methods.all().first() or \
            content_model.metadata.quality_levels.all().first():
        extended_metadata_exists = True

    wml2_url = ""
    for f in content_model.files.all():
        if 'visual' in str(f.resource_file.name):
            context['visfile'] = f
        if 'wml_2' in str(f.resource_file.name):
            wml2_url = f.resource_file.url

    for tool in context['relevant_tools']:
        tool['url'] = "{}{}{}".format(tool['url'], "&fileurl=", request.build_absolute_uri(wml2_url))
    context['extended_metadata_exists'] = extended_metadata_exists
    context['site'] = content_model.metadata.sites.all().first()
    context['variable'] = content_model.metadata.variables.all().first()
    context['method'] = content_model.metadata.methods.all().first()
    context['quality_level'] = content_model.metadata.quality_levels.all().first
    context['referenceURL'] = content_model.metadata.referenceURLs.all().first
    context['short_id'] = content_model.short_id
    return context



def update_files(request, shortkey, *args, **kwargs):

    ts_utils.generate_files(shortkey)
    # if files:
    #     if len(res.files.all())>0:
    #         for f in res.files.all():
    #             f.resource_file.delete()
    #     res_files = []
    #     for f in files:
    #         res_file = hydroshare.add_resource_files(res.short_id, f)[0]
    #         res_files.append(res_file)
    #         os.remove(f.name)
    #     for fl in res.files.all():
    #         if fl.resource_file:
    #             pass
    #         else:
    #             fl.delete()

        # # cap 3 bags per day, 5 overall
        # bag = ''
        # bag = create_bag(res)
        # if len(res.bags.all()) > 5:
        #     for b in res.bags.all()[5:]:
        #         b.delete()
        # for f in res_files:
        #     if str(f.resource_file).endswith('.csv'):
        #         csv_name = str(f.resource_file)
        #         sl_loc = csv_name.rfind('/')
        #         csv_name = csv_name[sl_loc+1:]
        #         csv_link = f.resource_file.url
        #         csv_size = f.resource_file.size
        #     if str(f.resource_file).endswith('.wml') and 'wml_2' in str(f.resource_file):
        #         wml2_name = str(f.resource_file)
        #         sl_loc = wml2_name.rfind('/')
        #         wml2_name = wml2_name[sl_loc+1:]
        #         wml2_link = f.resource_file.url
        #         wml2_size = f.resource_file.size
        #     if str(f.resource_file).endswith('.wml') and 'wml_1' in str(f.resource_file):
        #         wml1_name = str(f.resource_file)
        #         sl_loc = wml1_name.rfind('/')
        #         wml1_name = wml1_name[sl_loc+1:]
        #         wml1_link = f.resource_file.url
        #         wml1_size = f.resource_file.size
        #     if 'visual' in str(f.resource_file):
        #         vis_link = f.resource_file.url

    status_code = 200

        # #changing date to match Django formatting
        # time = bag.timestamp.date().strftime('%b. %d, %Y, %I:%M %P')
        # if time.endswith('am'):
        #     time = time[:-2]+'a.m.'
        # elif time.endswith('pm'):
        #     time = time[:-2]+'p.m.'

    return json_or_jsonp(request, status_code)  # successfully generated new files
