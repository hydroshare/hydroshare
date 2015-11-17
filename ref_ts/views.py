from __future__ import absolute_import

import tempfile, zipfile
import shutil
import requests
from lxml import etree
import ast

from django.contrib.auth.decorators import login_required
from django import forms
from django.http import HttpResponseRedirect, HttpResponseNotFound
from django.http import HttpResponse
from mezzanine.pages.page_processors import processor_for

from hs_core import hydroshare, page_processors
from ga_resources.utils import json_or_jsonp
from .models import RefTimeSeriesResource
from . import ts_utils

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

ts = None
preview_name = "preview.png"
def time_series_from_service(request):
    f = GetTSValuesForm(request.GET)
    if f.is_valid():
        params = f.cleaned_data
        ref_type = params['ref_type']
        url = params['service_url']
        site = params.get('site')
        variable = params.get('variable')
        global ts
        if ref_type == 'rest':
            ts = ts_utils.time_series_from_service(url, ref_type)
            site = ts.get('site_code')
        else:
            ts = ts_utils.time_series_from_service(url, ref_type, site_name_or_code=site, variable_code=variable)
        for_graph = ts['for_graph']
        units = ts['units']
        variable_name = ts['variable_name']
        noDataValue = ts.get('noDataValue', None)
        ts['url'] = url
        ts['ref_type'] = ref_type
        try:
            tempdir = tempfile.mkdtemp()
            vis_fn_fh_dict = ts_utils.create_vis(tempdir, site, for_graph, 'Date', variable_name, units, noDataValue,predefined_name=preview_name)
            vis_fn_fh_dict["fhandle"].close()
            tempdir_last_six_chars = tempdir[-6:]
            preview_url = "/hsapi/_internal/refts/preview-figure/%s/" % (tempdir_last_six_chars)
            return json_or_jsonp(request,{'preview_url': preview_url})
        except Exception as e:
            if tempdir is not None:
               shutil.rmtree(tempdir)
            raise e

def preview_figure (request, preview_code, *args, **kwargs):

    response = HttpResponse()
    try:
        tempdir_base_path = tempfile.gettempdir()
        tempdir_preview = tempdir_base_path + "/" + "tmp" + preview_code
        preview_full_path = tempdir_preview + "/" + preview_name
        preview_fhandle = open(preview_full_path,'rb')
        response.content_type = "image/png";
        response.write(str(preview_fhandle.read()))
        preview_fhandle["fhandle"].close()
        shutil.rmtree(tempdir_preview)
        return response
    except Exception as e:
        return response

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
    metadata = forms.CharField(required=False, min_length=0)
    title = forms.CharField(required=False, min_length=0)

@login_required
def create_ref_time_series(request, *args, **kwargs):
    url = ts['url']
    reference_type = ts['ref_type']
    frm = CreateRefTimeSeriesForm(request.POST)
    if frm.is_valid():
        metadata = frm.cleaned_data.get('metadata')
        metadata = ast.literal_eval(metadata)
        res = hydroshare.create_resource(
            resource_type='RefTimeSeriesResource',
            owner=request.user,
            title=frm.cleaned_data.get('title'),
            metadata=metadata,
            content= frm.cleaned_data.get('title')
        )

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
            name=ts['site_name'],
            code=ts['site_code'],
            latitude=ts['latitude'],
            longitude=ts['longitude']
        )

        hydroshare.resource.create_metadata_element(
            res.short_id,
            'Variable',
            name=ts['variable_name'],
            code=ts['variable_code'],
            sample_medium=ts.get('sample_medium', 'unknown')
        )
        #release global var
        global ts
        if ts is not None:
            ts = None
        return HttpResponseRedirect(res.get_absolute_url())

@processor_for(RefTimeSeriesResource)
def add_dublin_core(request, page):
    content_model = page.get_content_model()
    edit_resource = page_processors.check_resource_mode(request)
    context = page_processors.get_page_context(page, request.user, resource_edit=edit_resource, extended_metadata_layout=None, request=request)
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

    tools = context.get('relevant_tools')
    if tools:
        for tool in tools:
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

    ts_utils.generate_files(shortkey, ts=None)
    status_code = 200
    return json_or_jsonp(request, status_code)  # successfully generated new files


def download_files(request, shortkey, *args, **kwargs):
    try:
        from cStringIO import StringIO
    except ImportError:
        from io import BytesIO as StringIO

    tempdir = None
    try:
        tempdir = tempfile.mkdtemp()

        fn_fh_dic_arr = ts_utils.generate_files(shortkey, None, tempdir)
        in_memory_zip = StringIO()
        archive = zipfile.ZipFile(in_memory_zip, 'w', zipfile.ZIP_DEFLATED)
        for fn_fh_dic_item in fn_fh_dic_arr:
            archive.writestr(fn_fh_dic_item['fname'], fn_fh_dic_item['fhandle'].read())
            fn_fh_dic_item['fhandle'].close()
        archive.close()

        res = hydroshare.get_resource_by_shortkey(shortkey)
        response = HttpResponse(in_memory_zip.getvalue(), content_type='application/zip')
        response['Content-Disposition'] = 'attachment; filename="' + res.title.replace(" ","_") + '.zip"'
        response['Content-Length'] = len(in_memory_zip.getvalue())

        return response
    except Exception as e:
        raise e
    finally:
        if tempdir is not None:
           shutil.rmtree(tempdir)
        #release global var
        global ts
        if ts is not None:
            ts = None
