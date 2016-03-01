import json

from django.contrib import admin
from django.contrib.admin import ModelAdmin
from django.contrib.auth.models import Group
import importlib
from django.contrib.gis.geos import Polygon, GEOSGeometry
from django.apps import apps
from django.http import HttpResponseRedirect, HttpResponse, HttpResponseNotFound
from django.shortcuts import get_object_or_404
from ga_resources.models import DataResource
from mezzanine.core.forms import get_edit_form
from mezzanine.pages.models import Page
from mezzanine.utils.urls import admin_url
from .kmz import *
from .ows import *
from .rest_data import *

def to_referrer(request):
    return HttpResponseRedirect(request.META['HTTP_REFERER'])

def create_page(request):
    models = request.GET['module']
    pageclass = request.GET['classname']
    parent = request.GET['parent']

    parent = Page.objects.get(slug=parent).get_content_model()
    models = importlib.import_module(models)
    pageclass = getattr(models, pageclass)

    title = request.GET.get('title', "new " + pageclass._meta.object_name)
    # page = pageclass.objects.create(title=title, parent=parent)
    return HttpResponseRedirect(
        admin_url(pageclass, 'add') + "?parent={pk}&next={next}".format(pk=parent.pk, next=parent.get_absolute_url()))


def delete_page(request):
    slug = request.GET['slug']
    p = Page.objects.get(slug=slug)
    p.delete()
    return HttpResponseRedirect(request.META['HTTP_REFERER'])


def download_file(request, *args, **kwargs):
    slug, ext = kwargs['slug'].split('.')
    drv = get_object_or_404(DataResource, slug=slug)
    if drv.driver_instance.supports_download():
        rsp = HttpResponse(drv.driver_instance.filestream(), mimetype=drv.driver_instance.mimetype())
        rsp['Content-Disposition'] = 'attachment; filename="{filename}"'.format(
            filename=drv.slug.split('/')[-1] + '.' + ext)
        return rsp
    else:
        return HttpResponseNotFound()


def extent(request, *args, **kwargs):
    res = DataResource.objects.get(slug=kwargs['slug'])
    ret = res.spatial_metadata.bounding_box
    ret.transform(int(request.REQUEST.get('srid', 3857)))
    ret = ret.extent

    callback = None
    if 'jsonCallback' in request.REQUEST:
        callback = request.REQUEST['jsonCallback']
    elif 'callback' in request.REQUEST:
        callback = request.REQUEST['callback']

    if callback:
        return HttpResponse(callback + '(' + json.dumps(ret) + ")", mimetype='text/plain')
    else:
        return HttpResponse(json.dumps(ret), mimetype='application/json')


def search_catalog(request, *args, **kwargs):
    """A spatial search for the DataResource catalog. In the future, this will be more thorough, but right now it looks
    for a filter parameter in the request, and inside that a JSON payload including a bbox four-tuple of minx, maxx
     miny, maxy OR a geometry wkt and an optional srid.  It then performs a broad overlap search and returns the results
     as a JSON or JSONP list of::

        [{ "title" : "title",
           "path" : ["breadcrumps", "to", "resource"],
           "url" : "http://mydomain/ga_resources/path/to/resource/title"
        }]
    """
    flt = json.loads(request.REQUEST['filter'])
    if 'bbox' in flt:
        minx, miny, maxx, maxy = flt['bbox']
        geometry = Polygon.from_bbox((minx, miny, maxx, maxy))
    else:
        geometry = GEOSGeometry(flt['boundary'])

    if 'srid' in flt:
        geometry.set_srid(flt['srid'])

    results = DataResource.objects.filter(bounding_box__overlaps=geometry)
    ret = [{'title': r.title, 'path': r.slug.split('/')[:-1], 'url': r.get_abolute_url()} for r in results]

    callback = None
    if 'jsonCallback' in request.REQUEST:
        callback = request.REQUEST['jsonCallback']
    elif 'callback' in request.REQUEST:
        callback = request.REQUEST['callback']

    if callback:
        return HttpResponse(callback + '(' + json.dumps(ret) + ")", mimetype='text/plain')
    else:
        return HttpResponse(json.dumps(ret), mimetype='application/json')

def view_groups(request, *args, **kwargs):
    """View, add, or delete view groups
    :param request:  
    :param args: 
    :param kwargs: 
    :return:
    """
    page = Page.objects.get(slug=kwargs['slug']).get_content_model()
    
    if request.method == 'POST':
        try:
            page.add_view_group(Group.objects.get(name=request.POST['name']))
        except:
            pass
        return to_referrer(request)
    elif request.method == 'DELETE':
        try:
            grp = int(kwargs['group'])
            page.remove_view_group(Group.objects.get(pk=grp))
        except:
            grp = kwargs['group']
            page.remove_view_group(Group.objects.get(name=grp))
        return to_referrer(request)

    return json_or_jsonp(request, list(page.view_groups), 200)

def view_users(request, *args, **kwargs):
    """View, add, or delete view users
    :param request:  
    :param args: 
    :param kwargs: 
    :return:
    """

    page = Page.objects.get(slug=kwargs['slug']).get_content_model()
    
    if request.method == 'POST':
        try:
            page.add_view_user(User.objects.get(email=request.POST['name']))
        except:
            pass

        return to_referrer(request)
    elif request.method == 'DELETE':
        try:
            grp = int(kwargs['user'])
            page.remove_view_user(grp)
            print "removed user {u} from page {p}".format(u=grp, p=page.pk)
        except:
            grp = kwargs['user']
            page.remove_view_user(User.objects.get(email=grp))
        return to_referrer(request)

    return json_or_jsonp(request, list(page.view_users.union({page.owner.pk} if page.owner else set())), 200)

def edit_groups(request, *args, **kwargs):
    """View, add, or delete edit groups
    :param request:  
    :param args: 
    :param kwargs: 
    :return:
    """
    page = Page.objects.get(slug=kwargs['slug']).get_content_model()
    
    if request.method == 'POST':
        try:
            page.add_edit_group(Group.objects.get(name=request.POST['name']))
        except:
            pass
        return to_referrer(request)
    elif request.method == 'DELETE':
        try:
            grp = int(kwargs['group'])
            page.remove_edit_group(Group.objects.get(pk=grp))
        except:
            grp = kwargs['group']
            page.remove_edit_group(Group.objects.get(name=grp))
        return to_referrer(request)

    return json_or_jsonp(request, list(page.edit_groups), 200)

def edit_users(request, *args, **kwargs):
    """View, add, or delete edit users
    :param request:  
    :param args: 
    :param kwargs: 
    :return:
    """

    print kwargs
    page = Page.objects.get(slug=kwargs['slug']).get_content_model()
    
    if request.method == 'POST':
        try:
            page.add_edit_user(User.objects.get(email=request.POST['name']))
        except:
            pass # invalid email address - need to handle better

        return to_referrer(request)
    elif request.method == 'DELETE':
        try:
            grp = int(kwargs['user'])
            page.remove_edit_user(User.objects.get(pk=grp))
        except:
            grp = kwargs['user']
            page.remove_edit_user(User.objects.get(username=grp))
        return to_referrer(request)

    return json_or_jsonp(request, list(page.edit_users.union({page.owner.pk} if page.owner else set())), 200)


def edit(request):
    """
    Process the inline editing form.
    """
    model = apps.get_model(request.POST["app"], request.POST["model"])
    obj = model.objects.get(id=request.POST["id"])
    form = get_edit_form(obj, request.POST["fields"], data=request.POST,
                         files=request.FILES)

    authorize(request, obj)
    if form.is_valid():
        form.save()
        model_admin = ModelAdmin(model, admin.site)
        message = model_admin.construct_change_message(request, form, None)
        model_admin.log_change(request, obj, message)
        response = ""
    else:
        response = list(form.errors.values())[0][0]
    return HttpResponse(response)
