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
from django.shortcuts import render
from rest_framework.decorators import api_view

from hs_core import hydroshare
from hs_core.views.utils import authorize, ACTION_TO_AUTHORIZE, json_or_jsonp

from django_irods.views import download as download_bag_from_irods
from . import ts_utils
from .forms import ReferencedSitesForm, ReferencedVariablesForm, GetTSValuesForm, \
    VerifyRestUrlForm, CreateRefTimeSeriesForm

from drf_yasg.utils import swagger_auto_schema


PREVIEW_NAME = "preview.png"
HIS_CENTRAL_URL = 'http://hiscentral.cuahsi.org/webservices/hiscentral.asmx/GetWaterOneFlowServiceInfo'

logger = logging.getLogger(__name__)

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
            ts_utils.create_vis_2(path=tempdir, data=data, xlabel='Date',
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
            ts = requests.get(url, verify=False)
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


def download_refts_resource_bag(request, shortkey, *args, **kwargs):
    tempdir = None
    try:
        _, authorized, _ = authorize(request, shortkey,
                                     needed_permission=ACTION_TO_AUTHORIZE.VIEW_RESOURCE,
                                     raises_exception=False)
        if not authorized:
            response = HttpResponse(status=401)
            response.content = "<h3>You do not have permission to download this resource!</h3>"
            return response

        path = "bags/" + str(shortkey) + ".zip"
        response_irods = download_bag_from_irods(request, path, use_async=False,
                                                 use_reverse_proxy=False)

        tempdir = tempfile.mkdtemp()
        response = assemble_refts_bag(shortkey, response_irods.streaming_content,
                                      temp_dir=tempdir)

        return response
    except Exception as e:
        logger.exception("download_refts_resource_bag: %s" % (e.message))
        response = HttpResponse(status=503)
        response.content = "<h3>Failed to download this resource!</h3>"
        return response
    finally:
        if tempdir is not None:
           shutil.rmtree(tempdir)


@swagger_auto_schema(method='get', auto_schema=None)
@api_view(['GET'])
def rest_download_refts_resource_bag(request, shortkey, *args, **kwargs):
    tempdir = None
    _, authorized, _ = authorize(request, shortkey,
                                 needed_permission=ACTION_TO_AUTHORIZE.VIEW_RESOURCE,
                                 raises_exception=True)
    try:

        path = "bags/" + str(shortkey) + ".zip"
        response_irods = download_bag_from_irods(request, path, rest_call=True, use_async=False,
                                                 use_reverse_proxy=False)

        if not response_irods.streaming:
            raise Exception("Failed to stream RefTS bag")
        else:
            tempdir = tempfile.mkdtemp()
            response = assemble_refts_bag(shortkey, response_irods.streaming_content,
                                          temp_dir=tempdir)
            return response

    except Exception as e:
        logger.exception("rest_download_refts_resource_bag: %s" % (e.message))
        response = HttpResponse(status=503)
        response.content = "Failed to download this resource!"
        return response
    finally:
        if tempdir is not None:
           shutil.rmtree(tempdir)


def assemble_refts_bag(res_id, empty_bag_stream, temp_dir=None):
    """
    save empty_bag_stream to local; download latest wml;
    put wml into empty bag; return filled-in bag in FileResponse
    :param res_id: the resource id of the RefTS resource
    :param bag_stream: the stream of the empty bag
    :param temp_dir: a folder to store files locally
    :return: FileResponse obj
    """
    if temp_dir is None:
        temp_dir = tempfile.mkdtemp()
    bag_save_to_path = temp_dir + "/" + str(res_id) + ".zip"

    with open(bag_save_to_path, 'wb+') as f:
        for chunk in empty_bag_stream:
            f.write(chunk)

    res_files_fp_arr = ts_utils.generate_resource_files(res_id, temp_dir)

    bag_zip_obj = zipfile.ZipFile(bag_save_to_path, "a", zipfile.ZIP_DEFLATED)
    bag_content_base_folder = str(res_id) + "/data/contents/"  # _RESOURCE_ID_/data/contents/
    for fn_fp in res_files_fp_arr:
        fh = open(fn_fp['fullpath'], 'r')
        bag_zip_obj.writestr(bag_content_base_folder + fn_fp['fname'], fh.read())
        fh.close()
    bag_zip_obj.close()

    response = FileResponse(open(bag_save_to_path, 'rb'), content_type='application/zip')
    response['Content-Disposition'] = 'attachment; filename="' + str(res_id) + '.zip"'
    response['Content-Length'] = os.path.getsize(bag_save_to_path)

    return response
