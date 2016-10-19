from requests import put, delete, get
from requests.auth import HTTPBasicAuth
from celery import shared_task

import os
from subprocess import check_output
from StringIO import StringIO
from zipfile import ZipFile

endpoint = "http://apps.hydroshare.org:8181/geoserver/rest"
workspace = "hydroshare_resources"
username = 'admin'
password = 'hydroshare'


@shared_task
def add_ogc_services(resource):
    r = None

    if resource.resource_type.lower() == 'rasterresource':
        r = create_coverage_layer(resource)
    elif resource.resource_type.lower() == 'geographicfeatureresource':
        r = create_feature_layer(resource)

    if r and r['success']:
        metadata = r['results']['metadata']

        update_resource_ogc_metadata(resource, metadata)


@shared_task
def remove_ogc_services(resource):
    res_id = resource.short_id
    store_type = None
    params = {'recurse': 'true'}

    if resource.resource_type.lower() == 'rasterresource':
        store_type = 'coveragestores'
        params['purge'] = 'all'
    elif resource.resource_type.lower() == 'geographicfeatureresource':
        store_type = 'datastores'

    url = '{0}/workspaces/{1}/{2}/{3}'.format(endpoint, workspace, store_type, res_id)

    delete(url, params=params, auth=HTTPBasicAuth(username=username, password=password))


def create_coverage_layer(resource):
    return_obj = {
        'success': False,
        'results': {}
    }
    res_id = resource.short_id
    files = resource.files.all()
    coverage_type = None
    coverage_file = None
    content_type = None

    for f in files:
        if f.resource_file.name.endswith('.tif'):
            coverage_file = f.resource_file.file.name
            coverage_type = 'geotiff'
            content_type = 'image/geotiff'
            break

    r = check_crs('RasterResource', coverage_file)
    if r['success']:
        if r['crsWasChanged']:
            code = r['code']
            os.system('gdal_edit.py -a_srs {0} {1}'.format(code, coverage_file))

    data = open(coverage_file, 'rb')

    url = '{0}/workspaces/{1}/coveragestores/{2}/file.{3}'.format(endpoint, workspace, res_id,
                                                                  coverage_type)
    headers = {
        "Content-type": content_type
    }
    params = {
        'coverageName': res_id,
        'update': 'overwrite'
    }

    r = put(url=url,
            files=None,
            data=data,
            headers=headers,
            params=params,
            auth=HTTPBasicAuth(username=username,
                               password=password))

    if r.status_code == 200 or r.status_code == 201:
        return_obj['success'] = True
        return_obj['results']['metadata'] = {
            'wmsEndpoint': endpoint.replace('rest', 'wms'),
            'wcsEndpoint': endpoint.replace('rest', 'wcs'),
            'layerName': res_id
        }

    return return_obj


def create_feature_layer(resource):
    return_obj = {
        'success': False,
        'results': {}
    }
    res_id = resource.short_id
    files = resource.files.all()
    content_type = 'application/zip'
    shp_files = {
        '.shp': 'filepath',
        '.dbf': 'filepath',
        '.prj': 'filepath',
        '.shx': 'filepath'
    }

    for f in files:
        for ext in shp_files:
            if f.resource_file.name.endswith(ext):
                shp_files[ext] = f.resource_file.file.name
                break

    r = check_crs('GeographicFeatureResource', shp_files['.prj'])
    if r['success']:
        if r['crsWasChanged']:
            with open(shp_files['.prj'], 'w') as f:
                f.seek(0)
                f.write(r['new_wkt'])

    zip_file_in_memory = StringIO()

    with ZipFile(zip_file_in_memory, 'w') as zfile:
        for ext in shp_files:
            with open(shp_files[ext], 'rb') as f:
                zfile.writestr('%s%s' % (res_id, ext), f.read())

    url = '{0}/workspaces/{1}/datastores/{2}/file.shp'.format(endpoint, workspace, res_id)
    files = {'file': zip_file_in_memory.getvalue()}
    headers = {
        "Content-type": content_type
    }
    params = {
        'update': 'overwrite'
    }

    r = put(url=url,
            files=files,
            headers=headers,
            params=params,
            auth=HTTPBasicAuth(username=username,
                               password=password))

    if 200 <= r.status_code < 300:
        return_obj['success'] = True
        return_obj['results']['metadata'] = {
            'wmsEndpoint': endpoint.replace('rest', 'wms'),
            'wfsEndpoint': endpoint.replace('rest', 'wfs'),
            'layerName': res_id
        }

    return return_obj


def update_resource_ogc_metadata(resource, metadata):
    if resource.resource_type.lower() == 'rasterresource':
        md_id = resource.metadata.ogcWebServices.id
    else:
        md_id = resource.metadata.ogcWebServices.first().id
    resource.metadata.update_element("OGCWebServices", md_id, **metadata)


def check_crs(res_type, fpath):
    return_obj = {
        'success': False,
        'message': None,
        'code': None,
        'crsWasChanged': False,
        'new_wkt': None
    }

    if res_type == 'RasterResource':
        gdal_info = check_output('gdalinfo %s' % fpath, shell=True)
        start = 'Coordinate System is:'
        length = len(start)
        end = 'Origin ='
        if gdal_info.find(start) == -1:
            return_obj['message'] = 'There is no projection information associated with this resource.' \
                                    '\nResource cannot be added to the map project.'
            return return_obj
        start_index = gdal_info.find(start) + length
        end_index = gdal_info.find(end)
        crs_raw = gdal_info[start_index:end_index]
        crs = ''.join(crs_raw.split())
    else:
        with open(fpath) as f:
            crs = f.read()

    url = 'http://prj2epsg.org/search.json'
    params = {
        'mode': 'wkt',
        'terms': crs
    }
    crs_is_unknown = True
    try:
        while crs_is_unknown:
            r = get(url, params=params)
            if '50' in str(r.status_code):
                raise Exception
            elif r.status_code == 200:
                response = r.json()
                if 'errors' in response:
                    errs = response['errors']
                    if 'Invalid WKT syntax' in errs:
                        err = errs.split(':')[2]
                        if err and 'Parameter' in err:
                            crs_param = err.split('"')[1]
                            rm_indx_start = crs.find(crs_param)
                            rm_indx_end = None
                            sub_str = crs[rm_indx_start:]
                            counter = 0
                            check = False
                            for i, c in enumerate(sub_str):
                                if c == '[':
                                    counter += 1
                                    check = True
                                elif c == ']':
                                    counter -= 1
                                    check = True
                                if check:
                                    if counter == 0:
                                        rm_indx_end = i + rm_indx_start + 1
                                        break
                            crs = crs[:rm_indx_start] + crs[rm_indx_end:]
                            if ',' in crs[:-4]:
                                i = crs.rfind(',')
                                crs = crs[:i] + crs[i+1:]
                            params['terms'] = crs
                            return_obj['crsWasChanged'] = True
                        else:
                            break
                    else:
                        break
                else:
                    crs_is_unknown = False
                    code = response['codes'][0]['code']
                    if res_type == 'RasterResource':
                        if code not in crs:
                            return_obj['crsWasChanged'] = True
                            return_obj['code'] = 'EPSG:' + code
                    else:
                        if code not in crs:
                            return_obj['crsWasChanged'] = True
                            r = get(response['codes'][0]['url'])
                            proj_json = r.json()
                            raw_wkt = proj_json['wkt']
                            tmp_list = []
                            for seg in raw_wkt.split('\n'):
                                tmp_list.append(seg.strip())
                            return_obj['new_wkt'] = ''.join(tmp_list)

                    return_obj['success'] = True
            else:
                params['mode'] = 'keywords'
                continue
    except Exception as e:
        return_obj['message'] = str(e)

    return return_obj
