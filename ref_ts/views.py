from __future__ import absolute_import

import os
import tempfile
import zipfile
import shutil
import requests
from lxml import etree
import logging

from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseNotFound, FileResponse
from django.shortcuts import render_to_response

from hs_core import hydroshare
from hs_core.views.utils import authorize
from ga_resources.utils import json_or_jsonp
from django_irods.views import download as download_bag_from_irods
from . import ts_utils
from .forms import ReferencedSitesForm, ReferencedVariablesForm, GetTSValuesForm, VerifyRestUrlForm, CreateRefTimeSeriesForm

PREVIEW_NAME = "preview.png"
HIS_CENTRAL_URL = 'http://hiscentral.cuahsi.org/webservices/hiscentral.asmx/GetWaterOneFlowServiceInfo'
BLANK_FIELD_STRING = ""

logger = logging.getLogger("django")

# query HIS central to get all available HydroServer urls
def get_his_urls(request):
    try:
        r = requests.get(HIS_CENTRAL_URL)
        if r.status_code == 200:
            response = r.text.encode('utf-8')
            root = etree.XML(response)
        else:
            raise Exception("Query HIS central error.")
        url_list = []
        for element in root.iter():
            if "servURL" in element.tag:
                url_list.append(element.text)
        return json_or_jsonp(request, {"status": "success", "url_list": url_list})
    except Exception as e:
        logger.exception("get_his_urls: " + e.message)
        return json_or_jsonp(request, {"status": "error"})

def search_sites(request):
    try:
        f = ReferencedSitesForm(request.GET)
        if f.is_valid():
            params = f.cleaned_data
            url = params['url']
            sites = ts_utils.sites_from_soap(url)
            return json_or_jsonp(request, {"status": "success", "sites": sites})
        else:
            raise Exception("search_sites form validation failed.")
    except Exception as e:
        logger.exception("search_sites: " + e.message)
        return json_or_jsonp(request, {"status": "error"})

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
            raise Exception("search_variables form validation failed.")
    except Exception as e:
        logger.exception("search_variables: %s" % (e.message))
        return json_or_jsonp(request, {"status": "error"})

def time_series_from_service(request):
    tempdir = None
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
            ts_utils.create_vis_2(path=tempdir, site_name=site, data=data, xlabel='Date',
                                variable_name=variable_name, units=units, noDataValue=noDataValue,
                                predefined_name=PREVIEW_NAME)
            tempdir_last_six_chars = tempdir[-6:]
            preview_url = "/hsapi/_internal/refts/preview-figure/%s/" % (tempdir_last_six_chars)
            return json_or_jsonp(request, {'status': "success", 'preview_url': preview_url})
        else:
            raise Exception("GetTSValuesForm form validation failed.")
    except Exception as e:
        logger.exception("time_series_from_service: %s" % (e.message))
        if tempdir is not None:
           shutil.rmtree(tempdir)
        return json_or_jsonp(request, {'status': "error"})


def preview_figure(request, preview_code, *args, **kwargs):
    response = HttpResponse()
    preview_str = None
    tempdir_preview = None
    try:
        tempdir_base_path = tempfile.gettempdir()
        tempdir_preview = tempdir_base_path + "/" + "tmp" + preview_code
        preview_full_path = tempdir_preview + "/" + PREVIEW_NAME
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

def verify_rest_url(request):
    try:
        f = VerifyRestUrlForm(request.GET)
        if f.is_valid():
            params = f.cleaned_data
            url = params['url']
            ts = requests.get(url)
            ts_xml = etree.XML(ts.text.encode('utf-8'))
            if ts.status_code == 200 and 'timeseriesresponse' in ts_xml.tag.lower():
                return json_or_jsonp(request, {"status": "success"})
            elif ts.status_code == 200 and 'collection' in ts_xml.tag.lower():
                return json_or_jsonp(request, {"status": "success"})
            else:
                raise Exception("Test REST url failed.")
        else:
            raise Exception("Invalid REST url.")
    except:
        return json_or_jsonp(request, {"status": "error"})

@login_required
def create_ref_time_series(request, *args, **kwargs):
    try:
        ts_dict = request.session.get('ts', False)
        if not ts_dict:
            raise Exception("No ts in session")

        url = ts_dict['url']
        reference_type = ts_dict['ref_type']
        frm = CreateRefTimeSeriesForm(request.POST)
        if frm.is_valid():
            metadata = []
            if ts_dict["longitude"] is not None and ts_dict["latitude"] is not None:
                coverage_point = {"Coverage": {"type": "point",
                                      "value": {"east": ts_dict["longitude"],
                                                "north": ts_dict["latitude"],
                                                "units": "WGS 84 EPSG:4326"}
                                     }
                                 }
                metadata.append(coverage_point)

            if ts_dict["start_date"] is not None and ts_dict["end_date"] is not None:
                coverage_period ={"Coverage": {"type": "period",
                                      "value": {"start": ts_dict["start_date"],
                                                "end": ts_dict["end_date"]}
                                     }
                        }
                metadata.append(coverage_period)

            metadata += [{"ReferenceURL": {"value": url, "type": reference_type}},
                        {"Site": {"name": ts_dict['site_name'] if ts_dict['site_name'] is not None else BLANK_FIELD_STRING,
                                  "code": ts_dict['site_code'] if ts_dict['site_code'] is not None else BLANK_FIELD_STRING,
                                  "net_work": ts_dict['net_work'] if ts_dict['net_work'] is not None else BLANK_FIELD_STRING,
                                  "latitude": ts_dict['latitude'],
                                  "longitude": ts_dict['longitude']
                                  }
                        },
                        {"Variable": {"name": ts_dict['variable_name'] if ts_dict['variable_name'] is not None else BLANK_FIELD_STRING,
                                      "code": ts_dict['variable_code'] if ts_dict['variable_code'] is not None else BLANK_FIELD_STRING
                                      }
                        },
                        {"DataSource": {"code": ts_dict['source_code'] if ts_dict['source_code'] is not None else BLANK_FIELD_STRING}},
                        {"Method": {"code": ts_dict['method_code'] if ts_dict['method_code'] is not None else BLANK_FIELD_STRING,
                                    "description": ts_dict['method_description'] if ts_dict['method_description'] is not None else BLANK_FIELD_STRING
                                   }
                        },
                        {"QualityControlLevel": {
                            "code": ts_dict['quality_control_level_code'] if ts_dict['quality_control_level_code'] is not None else BLANK_FIELD_STRING,
                            "definition": ts_dict['quality_control_level_definition'] if ts_dict['quality_control_level_definition'] is not None else BLANK_FIELD_STRING
                                                 }
                        }]

            res = hydroshare.create_resource(
                resource_type='RefTimeSeriesResource',
                owner=request.user,
                title=frm.cleaned_data.get('title'),
                metadata=metadata)

            if ts_dict:
                del request.session['ts']

            request.session['just_created'] = True
            return HttpResponseRedirect(res.get_absolute_url())

    except Exception as ex:
        logger.exception("create_ref_time_series: %s" % (ex.message))
        context = {'resource_creation_error': "Error: failed to create resource." }
        return render_to_response('pages/create-ref-time-series.html', context, context_instance=RequestContext(request))

def download_refts_resource_files(request, shortkey, *args, **kwargs):
    tempdir = None
    try:
        _, authorized, _ = authorize(request, shortkey, edit=True, full=True, view=True, superuser=True, raises_exception=False)
        if not authorized:
            response = HttpResponse(status=401)
            response.content = "<h3>You do not have permission to download this resource!</h3>"
            return response

        path = "bags/" + str(shortkey) + ".zip"
        response_irods = download_bag_from_irods(request, path)

        tempdir = tempfile.mkdtemp()
        bag_save_to_path = tempdir + "/" + str(shortkey) + ".zip"

        with open(bag_save_to_path, 'wb+') as f:
            for chunk in response_irods.streaming_content:
                f.write(chunk)

        res_files_fp_arr = ts_utils.generate_resource_files(shortkey, tempdir)

        bag_zip_obj = zipfile.ZipFile(bag_save_to_path, "a", zipfile.ZIP_DEFLATED)
        bag_content_base_folder = str(shortkey) + "/data/contents/" # _RESOURCE_ID_/data/contents/
        for fn_fp in res_files_fp_arr:
            fh = open(fn_fp['fullpath'], 'r')
            bag_zip_obj.writestr(bag_content_base_folder + fn_fp['fname'], fh.read())
            fh.close()
        bag_zip_obj.close()

        response = FileResponse(open(bag_save_to_path, 'rb'), content_type='application/zip')
        response['Content-Disposition'] = 'attachment; filename="' + str(shortkey) + '.zip"'
        response['Content-Length'] = os.path.getsize(bag_save_to_path)

        return response
    except Exception as e:
        logger.exception("download_resource_files: %s" % (e.message))
        response = HttpResponse(status=503)
        response.content = "<h3>Failed to download this resource!</h3>"
        return response
    finally:
        if tempdir is not None:
           shutil.rmtree(tempdir)