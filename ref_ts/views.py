from __future__ import absolute_import

import os
import tempfile
import zipfile
import shutil
import requests
from lxml import etree
import ast
try:
    from cStringIO import StringIO
except ImportError:
    from io import BytesIO as StringIO

from django.contrib.auth.decorators import login_required
from django import forms
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseNotFound, Http404
from mezzanine.pages.page_processors import processor_for


from hs_core import hydroshare, page_processors
from ga_resources.utils import json_or_jsonp
from .models import RefTimeSeriesResource
from . import ts_utils, ReftsException

preview_name = "preview.png"

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
            ts = ts_utils.QueryHydroServerGetParsedWML(service_url=url, soap_or_rest=ref_type)
            site = ts.get('site_code')
        else:
            index = site.rfind(" [")
            site = site[index+2:len(site)-1]
            site_code = site

            index = variable.rfind(" [")
            variable_code = variable[index+2:len(variable)-1]

            ts = ts_utils.QueryHydroServerGetParsedWML(service_url=url, soap_or_rest=ref_type, site_code=site_code, \
                                                       variable_code=variable_code)
        ts['url'] = url
        ts['ref_type'] = ref_type

        ts_session = request.session.get('ts', None)
        if ts_session is not None:
            del request.session['ts']
        request.session['ts'] = ts

        data = ts['data']
        units = ts['unit_abbr']
        if units is None:
            units = ts['unit_name']
            if units is None:
                units = "Unknown"
        variable_name = ts['variable_name']
        noDataValue = ts['noDataValue']

        try:
            tempdir = tempfile.mkdtemp()
            vis_fn_fpath = ts_utils.create_vis_2(path=tempdir, site_name=site, data=data, xlabel='Date', \
                                                variable_name=variable_name, units=units, noDataValue=noDataValue, \
                                                predefined_name=preview_name)
            tempdir_last_six_chars = tempdir[-6:]
            preview_url = "/hsapi/_internal/refts/preview-figure/%s/" % (tempdir_last_six_chars)
            return json_or_jsonp(request, {'preview_url': preview_url})
        except Exception as e:
            if tempdir is not None:
               shutil.rmtree(tempdir)
            return json_or_jsonp(request, {'status': "error", 'preview_url': preview_url})


def preview_figure (request, preview_code, *args, **kwargs):

    response = HttpResponse()
    preview_str = None
    tempdir_preview = None
    try:
        tempdir_base_path = tempfile.gettempdir()
        tempdir_preview = tempdir_base_path + "/" + "tmp" + preview_code
        preview_full_path = tempdir_preview + "/" + preview_name
        preview_fhandle = open(preview_full_path,'rb')
        preview_str = str(preview_fhandle.read())
        preview_fhandle.close()
        if preview_str is None:
            raise
    except Exception as e:
        module_dir = os.path.dirname(__file__)
        error_location = os.path.join(module_dir, "static/ref_ts/img/warning.png")
        err_hdl = open(error_location, 'rb')
        preview_str = str(err_hdl.read())
        err_hdl.close()
    finally:
        if tempdir_preview is not None and os.path.isdir(tempdir_preview):
            shutil.rmtree(tempdir_preview)
        response.content_type = "image/png"
        response.write(preview_str)
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
    ts_dict = request.session.get('ts', False)
    if not ts_dict:
        raise ReftsException("No ts in session")

    url = ts_dict['url']
    reference_type = ts_dict['ref_type']
    frm = CreateRefTimeSeriesForm(request.POST)
    if frm.is_valid():
        metadata = frm.cleaned_data.get('metadata')
        metadata = ast.literal_eval(metadata)
        metadata = [{"Coverage": {"type": "point",
                                  "value": {"east": ts_dict["longitude"],
                                            "north": ts_dict["latitude"],
                                            "units": "WGS 84 EPSG:4326"}
                                 }
                     },
                    {"Coverage": {"type": "period",
                                  "value": {"start": ts_dict["start_date"],
                                            "end": ts_dict["end_date"]}
                                 }
                    }]

        res = hydroshare.create_resource(
            resource_type='RefTimeSeriesResource',
            owner=request.user,
            title=frm.cleaned_data.get('title'),
            metadata=metadata,
            content=frm.cleaned_data.get('title')
        )

        hydroshare.resource.create_metadata_element(
            res.short_id,
            'QualityControlLevel',
             code=ts_dict['quality_control_level_code'],
             definition=ts_dict['quality_control_level_definition'],
            )

        hydroshare.resource.create_metadata_element(
            res.short_id,
            'DataSource',
             code=ts_dict['source_code'],
            )

        hydroshare.resource.create_metadata_element(
            res.short_id,
            'Method',
            code=ts_dict['method_code'],
            description=ts_dict['method_description'],
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
            name=ts_dict['site_name'],
            code=ts_dict['site_code'],
            net_work=ts_dict['net_work'],
            latitude=ts_dict['latitude'],
            longitude=ts_dict['longitude']
        )

        hydroshare.resource.create_metadata_element(
            res.short_id,
            'Variable',
            name=ts_dict['variable_name'],
            code=ts_dict['variable_code'],
            sample_medium=ts_dict.get('sample_medium', 'unknown')
        )

        if ts_dict:
            del request.session['ts']

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
    wml2_fn = ""
    for f in content_model.files.all():
        if 'visual' in str(f.resource_file.name):
            context['visfile'] = f
        if 'wml_2' in str(f.resource_file.name):
            wml2_fn = f.resource_file.name
            wml2_url = f.resource_file.url
    wml2_fn_arr=wml2_fn.split('/')
    wml2_fn=wml2_fn_arr[-1]
    tools = context.get('relevant_tools')
    if tools:
        for tool in tools:
            tool['url'] = "{0}{1}{2}".format(tool['url'],"&fn=",wml2_fn)
    context['extended_metadata_exists'] = extended_metadata_exists
    context['site'] = content_model.metadata.sites.all().first()
    context['variable'] = content_model.metadata.variables.all().first()
    context['method'] = content_model.metadata.methods.all().first()
    context['quality_level'] = content_model.metadata.quality_levels.all().first
    context['referenceURL'] = content_model.metadata.referenceURLs.all().first
    context['short_id'] = content_model.short_id
    return context


def download_resource_files(request, shortkey, *args, **kwargs):

    tempdir = None
    try:
        tempdir = tempfile.mkdtemp()
        res_files_fp_arr = ts_utils.generate_resource_files(shortkey, tempdir)

        in_memory_zip = StringIO()
        archive = zipfile.ZipFile(in_memory_zip, 'w', zipfile.ZIP_DEFLATED)
        for fn_fp in res_files_fp_arr:
            fh = open(fn_fp['fullpath'], 'r')
            archive.writestr(fn_fp['fname'], fh.read())
            fh.close()
        archive.close()

        res = hydroshare.get_resource_by_shortkey(shortkey)
        response = HttpResponse(in_memory_zip.getvalue(), content_type='application/zip')
        response['Content-Disposition'] = 'attachment; filename="' + res.title.replace(" ", "_") + '.zip"'
        response['Content-Length'] = len(in_memory_zip.getvalue())

        return response
    except Exception as e:
        raise e
    finally:
        if tempdir is not None:
           shutil.rmtree(tempdir)
