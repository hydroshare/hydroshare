from __future__ import absolute_import

import os
import tempfile
import zipfile
import shutil
import requests
from lxml import etree
import ast
import logging
try:
    from cStringIO import StringIO
except ImportError:
    from io import BytesIO as StringIO


from django.contrib.auth.decorators import login_required
from django import forms
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseNotFound, Http404

from hs_core import hydroshare
from ga_resources.utils import json_or_jsonp
from . import ts_utils, ReftsException

preview_name = "preview.png"
his_central_url = 'http://hiscentral.cuahsi.org/webservices/hiscentral.asmx/GetWaterOneFlowServiceInfo'
logger = logging.getLogger(__name__)

# query HIS central to get all available HydroServer urls
def get_his_urls(request):
    try:
        r = requests.get(his_central_url)
        if r.status_code == 200:
            response = r.text.encode('utf-8')
            root = etree.XML(response)
        else:
            raise
        url_list = []
        for element in root.iter():
            if "servURL" in element.tag:
                url_list.append(element.text)
        return json_or_jsonp(request, {"status": "success", "url_list": url_list})
    except Exception as e:
        logger.exception("get_his_urls: " + e.message)
        return json_or_jsonp(request, {"status": "error"})

class ReferencedSitesForm(forms.Form):
    url = forms.URLField()

def search_sites(request):
    try:
        f = ReferencedSitesForm(request.GET)
        if f.is_valid():
            params = f.cleaned_data
            url = params['url']
            sites = ts_utils.sites_from_soap(url)
            return json_or_jsonp(request, {"status": "success", "sites": sites})
        else:
            raise
    except Exception as e:
            logger.exception("search_sites: " + e.message)
            return json_or_jsonp(request, {"status": "error"})


class ReferencedVariablesForm(forms.Form):
    url = forms.URLField()
    site = forms.CharField(min_length=0)

def search_variables(request):
    try:
        f = ReferencedVariablesForm(request.GET)
        if f.is_valid():
            params = f.cleaned_data
            url = params['url']
            site = params['site']
            variables = ts_utils.site_info_from_soap(url, site=site)
            return json_or_jsonp(request, {"status": "success", "variables": variables})
        else:
            raise
    except Exception as e:
        return json_or_jsonp(request, {"status": "error"})


class GetTSValuesForm(forms.Form):
    ref_type = forms.CharField(min_length=0, required=True)
    service_url = forms.CharField(min_length=0, required=True)
    site = forms.CharField(min_length=0, required=False)
    variable = forms.CharField(min_length=0, required=False)

def time_series_from_service(request):
    try:
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

            tempdir = tempfile.mkdtemp()
            ts_utils.create_vis_2(path=tempdir, site_name=site, data=data, xlabel='Date', \
                                                variable_name=variable_name, units=units, noDataValue=noDataValue, \
                                                predefined_name=preview_name)
            tempdir_last_six_chars = tempdir[-6:]
            preview_url = "/hsapi/_internal/refts/preview-figure/%s/" % (tempdir_last_six_chars)
            return json_or_jsonp(request, {'status': "success",'preview_url': preview_url})
        else:
            raise
    except Exception as e:
        if tempdir is not None:
           shutil.rmtree(tempdir)
        return json_or_jsonp(request, {'status': "error"})


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
                    },
                    {"ReferenceURL": {"value": url, "type": reference_type}},
                    {"Site": {"name": ts_dict['site_name'],
                              "code": ts_dict['site_code'],
                              "net_work": ts_dict['net_work'],
                              "latitude": ts_dict['latitude'],
                              "longitude": ts_dict['longitude']}},
                    {"Variable": {"name": ts_dict['variable_name'],
                                  "code": ts_dict['variable_code'],
                                  "sample_medium": ts_dict.get('sample_medium', 'unknown')}},
                    {"DataSource": {"code": ts_dict['source_code']}},
                    {"Method": {"code": ts_dict['method_code'], "description": ts_dict['method_description']}},
                    {"QualityControlLevel": {"code": ts_dict['quality_control_level_code'],
                                             "definition": ts_dict['quality_control_level_definition']}}
                    ]

        res = hydroshare.create_resource(
            resource_type='RefTimeSeriesResource',
            owner=request.user,
            title=frm.cleaned_data.get('title'),
            metadata=metadata,
            content=frm.cleaned_data.get('title')
        )

        if ts_dict:
            del request.session['ts']

        return HttpResponseRedirect(res.get_absolute_url())

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
