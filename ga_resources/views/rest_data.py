from tempfile import NamedTemporaryFile
import json

from django.contrib.gis.geos import GEOSGeometry
import pandas
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View
from django.contrib.auth.models import User
from ga_resources.drivers.spatialite import SpatialiteDriver
from ga_resources.models import DataResource
from mezzanine.pages.models import Page
from tastypie.models import ApiKey
from ga_resources import dispatch
from ga_resources.utils import authorize, get_data_page_for_user, json_or_jsonp


def get_user(request):
    if 'api_key' in request.REQUEST:
        api_key = ApiKey.objects.get(key=request.REQUEST['api_key'])
        return api_key.user
    elif request.user.is_authenticated():
        return User.objects.get(pk=request.user.pk)
    else:
        return request.user




def create_dataset(request):
    user = authorize(request)

    title = request.REQUEST.get('title','Untitled dataset')
    srid = int(request.REQUEST.get('srid', 4326))
    geometry_type=request.REQUEST.get('geometry_type', 'GEOMETRY')
    columns_definitions=json.loads(request.REQUEST.get('columns_definitions', "{}"))
    columns_definitions=((key, value) for key, value in columns_definitions.items())

    if 'parent' in request.REQUEST:
        parent = Page.objects.get(slug=request.REQUEST['parent'])
        authorize(request, parent, add=True)
    else:
        parent = get_data_page_for_user(request.user)

    ds = SpatialiteDriver.create_dataset(
        title=title,
        parent=parent,
        srid=srid,
        geometry_type=geometry_type,
        columns_definitions=columns_definitions,
        owner=request.user
    )

    dispatch.api_accessed.send(sender=DataResource, instance=ds, user=user)
    dispatch.dataset_created.send(sender=DataResource, instance=ds, user=user)
    return json_or_jsonp(request, {'path' : ds.slug }, code=201)

def derive_dataset(request, slug):
    user = authorize(request)

    title = request.REQUEST.get('title', 'Untitled dataset')
    parent_dataresource=slug

    if 'parent_page' in request.REQUEST:
        parent_page = Page.objects.get(slug=request.REQUEST['parent_page'])
        authorize(request, parent_page, add=True)
    else:
        parent_page = get_data_page_for_user(request.user)

    parent_dataresource = DataResource.objects.get(slug=parent_dataresource)
    authorize(request, parent_dataresource, view=True)

    ds = SpatialiteDriver.derive_dataset(
        title=title,
        parent_page=parent_page,
        parent_dataresource=parent_dataresource,
        owner=request.user
    )

    dispatch.api_accessed.send(sender=DataResource, instance=ds, user=user)
    dispatch.dataset_created.send(sender=DataResource, instance=ds, user=user)
    return json_or_jsonp(request, {'path': ds.slug}, code=201)

def create_dataset_with_parent_geometry(request, slug):
    user = authorize(request)

    title = request.REQUEST.get('title', 'Untitled dataset')
    parent_dataresource = slug
    srid = int(request.REQUEST.get('srid', 4326))
    geometry_type = request.REQUEST.get('geometry_type', 'GEOMETRY')
    columns_definitions = json.loads(request.REQUEST.get('columns_definitions', "{}"))
    columns_definitions = ((key, value) for key, value in columns_definitions.items())
    parent_key = request.REQUEST.get('parent_key', None)
    child_key = request.REQUEST.get('child_key', None)
    csv = None

    if len(request.FILES.keys()) > 0:
        csvfile = NamedTemporaryFile(suffix='csv')
        csvfile.write(request.FILES[request.FILES.keys().next()].read())
        csvfile.flush()
        csv = pandas.DataFrame.from_csv(csvfile.name)

    if 'parent_page' in request.REQUEST:
        parent_page = Page.objects.get(slug=request.REQUEST['parent_page'])
        authorize(request, parent_page, add=True)
    else:
        parent_page = get_data_page_for_user(request.user)

    parent_dataresource = DataResource.objects.get(slug=parent_dataresource)
    authorize(request, parent_page, view=True)

    if csv:
        ds = SpatialiteDriver.join_data_with_existing_geometry(
            title=title,
            parent=parent_page,
            new_data=csv,
            join_field_in_existing_data=parent_key,
            join_field_in_new_data=child_key,
            parent_dataresource=parent_dataresource,
            srid=srid,
            geometry_type=geometry_type,
            owner=request.user
        )
    else:
        ds = SpatialiteDriver.create_dataset_with_parent_geometry(
            title=title,
            parent=parent_page,
            parent_dataresource=parent_dataresource,
            srid=srid,
            columns_definitions=columns_definitions,
            geometry_type=geometry_type,
            owner=request.user
        )

    dispatch.api_accessed.send(sender=DataResource, instance=ds, user=user)
    dispatch.dataset_created.send(sender=ds, user=user)
    return json_or_jsonp(request, {'path': ds.slug}, code=201)


def schema(request, slug=None, *args, **kwargs):
    s = get_object_or_404(DataResource, slug=slug)
    user = authorize(request, s, view=True)

    r = [{'name': n} for n in s.driver_instance.schema()]
    dispatch.api_accessed.send(sender=DataResource, instance=s, user=user)
    return json_or_jsonp(request, r)

@csrf_exempt
def add_column(request, slug=None, *args, **kwargs):
    field_name = request.REQUEST['name']
    field_type = request.REQUEST.get('type', 'text')
    ds = get_object_or_404(DataResource, slug=slug)
    user = authorize(request, ds, edit=True)

    ds.driver_instance.add_column(field_name, field_type)
    dispatch.api_accessed.send(sender=DataResource, instance=ds, user=user)
    dispatch.dataset_column_added.send(sender=DataResource, instance=ds, user=user)
    return HttpResponse(status=201)

@csrf_exempt
def add_row(request, slug=None, *args, **kwargs):
    ds = get_object_or_404(DataResource, slug=slug)
    user = authorize(request, ds, edit=True)

    schema = {k for k in ds.driver_instance.schema()}
    row = {k: v for k, v in request.REQUEST.items() if k in schema}

    try:
        payload = json.loads(request.body)
        for k in [x for x in payload if x in schema]:
            row[k] = payload[k]
    except:
        pass # just in case there's JSON in the payuload

    new_rec = ds.driver_instance.add_row(**row)
    bbox = GEOSGeometry(row['GEOMETRY']).envelope

    dispatch.api_accessed.send(sender=DataResource, instance=ds, user=user)
    dispatch.features_created.send(sender=DataResource, instance=ds, user=user, count=1, bbox=bbox)
    return json_or_jsonp(request, new_rec, code=201)

@csrf_exempt
def update_row(request, slug=None, ogc_fid=None, *args, **kwargs):
    ds = get_object_or_404(DataResource, slug=slug)
    user = authorize(request, ds, edit=True)

    schema = {k for k in ds.driver_instance.schema()}
    row = { k : v for k, v in request.REQUEST.items() if k in schema }
    try:
        payload = json.loads(request.body)
        for k in [x for x in payload if x in schema]:
            row[k] = payload[k]
    except:
        pass # just in case there's JSON in the payuload

    if ogc_fid is None:
        ogc_fid = row['OGC_FID']

    bbox = GEOSGeometry(ds.driver_instance.get_row(int(ogc_fid), geometry_format='wkt')['GEOMETRY']).envelope
    result = ds.driver_instance.update_row(int(ogc_fid), **row)
    dispatch.api_accessed.send(sender=DataResource, instance=ds, user=user)
    dispatch.features_updated.send(sender=DataResource, instance=ds, user=user, count=1, fid=ogc_fid, bbox=bbox)
    return json_or_jsonp(request, result)

@csrf_exempt
def delete_row(request, slug=None, ogc_fid=None, *args, **kwargs):
    ds = get_object_or_404(DataResource, slug=slug)
    bbox = GEOSGeometry(ds.driver_instance.get_row(int(ogc_fid), geometry_format='wkt')['GEOMETRY']).envelope
    ds.driver_instance.delete_row(int(ogc_fid))
    user = authorize(request, ds, edit=True)

    dispatch.api_accessed.send(sender=DataResource, instance=ds, user=user)
    dispatch.features_deleted.send(sender=DataResource, instance=ds, user=user, count=1, fid=ogc_fid, bbox=bbox)
    return HttpResponse()


def get_row(request, slug=None, ogc_fid=None, *args, **kwargs):
    ds = get_object_or_404(DataResource, slug=slug)
    ds.driver_instance.ready_data_resource()
    user = authorize(request, ds, view=True)

    format = request.REQUEST.get('format', 'wkt')
    try:
        row = ds.driver_instance.get_row(int(ogc_fid), geometry_format=format)
    except:
        row = None

    dispatch.api_accessed.send(sender=DataResource, instance=ds, user=user)
    dispatch.features_retrieved.send(sender=DataResource, instance=ds, user=user, count=1, fid=ogc_fid)
    return json_or_jsonp(request, row)


def get_rows(request, slug=None, ogc_fid_start=None, ogc_fid_end=None, limit=None, *args, **kwargs):
    ds = get_object_or_404(DataResource, slug=slug)
    user = authorize(request, ds, view=True)
    ds.driver_instance.ready_data_resource()
    format = request.REQUEST.get('format', 'wkt')

    if ogc_fid_end:
        rows = ds.driver_instance.get_rows(int(ogc_fid_start), int(ogc_fid_end), geometry_format=format)
    elif limit:
        rows = ds.driver_instance.get_rows(int(ogc_fid_start), limit=int(limit), geometry_format=format)
    else:
        rows = ds.driver_instance.get_rows(int(ogc_fid_start), geometry_format=format)

    dispatch.api_accessed.send(sender=DataResource, instance=ds, user=user)
    dispatch.features_retrieved.send(sender=DataResource, instance=ds, user=user, count=len(rows))
    return json_or_jsonp(request, rows)


def query(request, slug=None, **kwargs):
    ds = get_object_or_404(DataResource, slug=slug)
    user = authorize(request, ds, view=True)

    ds.driver_instance.ready_data_resource()
    maybeint = lambda x: int(x) if x else None

    geometry_mbr = [float(kwargs[k]) for k in ['x1', 'y1', 'x2', 'y2']] if 'x1' in kwargs else None
    srid = kwargs['srid'] if 'srid' in kwargs else None
    geometry = request.REQUEST.get('g', None)
    geometry_format = request.REQUEST.get('format', 'geojson')
    geometry_operator = request.REQUEST.get('op', 'intersects')
    limit = maybeint(request.REQUEST.get('limit', None))
    start = maybeint(request.REQUEST.get('start', None))
    end = maybeint(request.REQUEST.get('end', None))
    only = request.REQUEST.get('only', None)
    if only:
        only = only.split(',')

    rest = {k: v for k, v in request.REQUEST.items() if
            k not in {'limit', 'start', 'end', 'only', 'g', 'op', 'format'}}

    rows = ds.driver_instance.query(
        query_mbr=geometry_mbr,
        query_geometry=geometry,
        geometry_format=geometry_format,
        geometry_operator=geometry_operator,
        query_geometry_srid=srid,
        limit=limit,
        start=start,
        end=end,
        only=only,
        **rest
    )

    dispatch.api_accessed.send(sender=DataResource, instance=ds, user=user)
    dispatch.features_retrieved.send(sender=DataResource, instance=ds, user=user, count=len(rows))
    return json_or_jsonp(request, rows)


class CRUDView(View):
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super(CRUDView, self).dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        if 'ogc_fid' in kwargs:
            return get_row(request, slug=kwargs['slug'], ogc_fid=kwargs['ogc_fid'])
        elif 'ogc_fid_start' in kwargs:
            return get_rows(
                request,
                slug=kwargs['slug'],
                ogc_fid_start=kwargs['ogc_fid_start'],
                ogc_fid_end=kwargs.get('ogc_fid_end', None),
                limit=kwargs.get('limit', None),
            )
        else:
            return query(
                request,
                slug=kwargs['slug'],
                **request.GET
            )

    def post(self, request, *args, **kwargs):
        return add_row(request, kwargs['slug'])

    def put(self, request, *args, **kwargs):
        return update_row(request, kwargs['slug'], kwargs.get('ogc_fid', None))

    def delete(self, request, *args, **kwargs):
        return delete_row(request, kwargs['slug'], kwargs.get('ogc_fid', None))

