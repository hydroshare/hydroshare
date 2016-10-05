from requests import put
from requests.auth import HTTPBasicAuth
from celery import shared_task
from hs_geo_raster_resource.models import RasterResource
from hs_geographic_feature_resource.models import GeographicFeatureResource

endpoint = "http://apps.hydroshare.org:8181/geoserver/rest"
workspace = "hydroshare_resources"
username = 'admin'
password = 'hydroshare'


@shared_task
def create_ogc_service(resource):
    r = None

    if type(resource) == RasterResource:
        r = create_coverage_layer(resource)
    elif type(resource) == GeographicFeatureResource:
        r = create_feature_layer(resource)

    if r and r['success']:
        metadata = r['results']['metadata']

        update_resource_ogc_metadata(resource, metadata)


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

    url = '{0}/workspaces/{1}/coveragestores/{2}/file.{3}'.format(endpoint, workspace, res_id,
                                                                  coverage_type)
    data = open(coverage_file, 'rb')

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

    return return_obj


def update_resource_ogc_metadata(resource, metadata):
    md_id = resource.metadata.ogcWebServices.id
    resource.metadata.update_element("OGCWebServices", md_id, **metadata)
