from requests import put, delete, get
from requests.auth import HTTPBasicAuth
from celery import shared_task
from django.conf import settings
from subprocess import check_output
from StringIO import StringIO
from zipfile import ZipFile
from shutil import rmtree
import os

endpoint = getattr(settings, "GEOSERVER_ENDPOINT", "https://appsdev.hydroshare.org:8443/geoserver/rest")
workspace = getattr(settings, "GEOSERVER_WORKSPACE", "hydroshare_resources")
username = getattr(settings, "GEOSERVER_USERNAME", "admin")
password = getattr(settings, "GEOSERVER_PASSWORD", "geoserver")

preview_res_layer_url_pattern = "{wms_endpoint}?service=WMS&version=1.1.0&request=GetMap&" \
                                "layers=hydroshare_resources:{layer_name}&styles=&bbox={bbox}&width=420&height=512&" \
                                "srs=EPSG:{epsg_code}&format=application/openlayers"


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
    res_files = resource.files.all()
    pyramid_dir_path = None
    tif_path = None
    data = None
    files = None
    epsg_code = None
    flag_check_crs = True
    num_files = 0
    tif_paths = []

    for f in res_files:
        num_files += 1

        if f.resource_file.name.endswith('.tif'):
            tif_path = f.resource_file.file.name
            tif_paths.append(tif_path)
            if flag_check_crs:
                flag_check_crs = False
                r = check_crs('RasterResource', tif_path)

                if r['success']:

                    if r['crsWasChanged']:
                        epsg_code = r['code']

            if epsg_code:
                os.system('gdal_edit.py -a_srs {0} {1}'.format(epsg_code, tif_path))

    if num_files > 2:
        pyramid_dir_path = '/tmp/%s/' % res_id
        os.mkdir(pyramid_dir_path)
        gdal_retile = 'gdal_retile.py -levels 9 -ps 2048 2048 -co "TILED=YES" -targetDir %s %s'
        os.system(gdal_retile % (pyramid_dir_path, ' '.join(tif_paths)))
        parent_folder = os.path.dirname(pyramid_dir_path)
        contents = os.walk(pyramid_dir_path)
        zip_file_in_memory = StringIO()

        with ZipFile(zip_file_in_memory, 'w') as zfile:
            for root, folders, files in contents:
                for folder_name in folders:
                    absolute_path = os.path.join(root, folder_name)
                    relative_path = absolute_path.replace(parent_folder + '/', '')
                    zfile.write(absolute_path, relative_path)
                for file_name in files:
                    absolute_path = os.path.join(root, file_name)
                    relative_path = absolute_path.replace(parent_folder + '/', '')
                    zfile.write(absolute_path, relative_path)

        content_type = 'application/zip'
        coverage_type = 'imagepyramid'
        files = {'file': zip_file_in_memory.getvalue()}

    else:
        coverage_type = 'geotiff'
        content_type = 'image/geotiff'
        data = open(tif_path, 'rb')

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
            files=files,
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

    if pyramid_dir_path and os.path.exists(pyramid_dir_path):
        rmtree(pyramid_dir_path, True)

    return return_obj


def create_feature_layer(resource):
    return_obj = {
        'success': False,
        'results': {}
    }
    res_id = resource.short_id
    files = resource.files.all()
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
        "Content-type": 'application/zip'
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
        'code': None,
        'crsWasChanged': False,
        'new_wkt': None
    }
    crs = get_crs_from_resource(res_type, fpath)
    if not crs:
        reproject_to_3857(fpath)
        return_obj['success'] = True
        return return_obj

    code = get_epsg_code_from_wkt(crs)

    if not code:
        reproject_to_3857(fpath)
        return_obj['success'] = True
        return return_obj

    if res_type == 'RasterResource':
        if code not in crs:
            return_obj['crsWasChanged'] = True
            return_obj['code'] = 'EPSG:' + code
    else:
        if code not in crs:
            return_obj['crsWasChanged'] = True
            wkt = get_wkt_from_epsg_code(code)
            return_obj['new_wkt'] = wkt

    return_obj['success'] = True

    return return_obj


def get_crs_from_resource(res_type, fpath):
    crs = None
    if res_type == 'RasterResource':
        gdal_info = check_output('gdalinfo %s' % fpath, shell=True)
        start = 'Coordinate System is:'
        length = len(start)
        end = 'Origin ='

        if gdal_info.find(start) == -1:
            return None

        start_index = gdal_info.find(start) + length
        end_index = gdal_info.find(end)
        crs_raw = gdal_info[start_index:end_index]
        crs = ''.join(crs_raw.split())
    else:
        with open(fpath) as f:
            crs = f.read()

    return crs


def get_epsg_code_from_wkt(wkt):
    code = None
    url = 'http://prj2epsg.org/search.json'
    params = {
        'mode': 'wkt',
        'terms': wkt
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
                                crs = crs[:i] + crs[i + 1:]
                            params['terms'] = crs
                        else:
                            break
                    else:
                        break
                else:
                    crs_is_unknown = False
                    codes = response['codes']
                    if len(codes) != 0:
                        code = response['codes'][0]['code']
            else:
                params['mode'] = 'keywords'
                continue
    except Exception as e:
        str(e)
        code = None

    return code


def get_wkt_from_epsg_code(code):
    url = 'http://prj2epsg.org/epsg/%s.json' % code
    r = get(url)
    proj_json = r.json()
    raw_wkt = proj_json['wkt']
    tmp_list = []

    for seg in raw_wkt.split('\n'):
        tmp_list.append(seg.strip())

    wkt = ''.join(tmp_list)

    return wkt


def reproject_to_3857(fpath):
    new_fpath = fpath + '_reprojected'
    os.system('gdal_translate -a_srs {0} {1} {2}'.format('EPSG:3857', fpath, new_fpath))
    print os.listdir('/tmp/')
    os.remove(fpath)
    os.rename(new_fpath, fpath)


def get_ogc_layer_bbox(res_id, res_type):
    bbox = None
    try:
        if res_type.lower() == 'rasterresource':
            store_type = 'coveragestores'
            store_name = 'coverages'
        else:
            store_type = 'datastores'
            store_name = 'featuretypes'

        url = '{0}/workspaces/{1}/{2}/{3}/{4}/{5}.json'.format(endpoint,
                                                               workspace,
                                                               store_type,
                                                               res_id,
                                                               store_name,
                                                               res_id)
        r = get(url, auth=(username, password))
        if r.status_code != 200:
            return
        else:
            json = r.json()

            if res_type == 'GeographicFeatureResource':
                extents = json['featureType']['latLonBoundingBox']
            else:
                extents = json['coverage']['latLonBoundingBox']

        bbox = {
            'westlimit': extents['minx'],
            'southlimit': extents['miny'],
            'eastlimit': extents['maxx'],
            'northlimit': extents['maxy']
        }
    except Exception:
        pass

    return bbox
