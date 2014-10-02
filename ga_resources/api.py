from tastypie.api import Api
from tastypie.fields import ForeignKey, ManyToManyField
from tastypie.resources import ModelResource, ALL, ALL_WITH_RELATIONS
from tastypie.authentication import SessionAuthentication
from tastypie.authorization import Authorization

from ga_resources import models
from mezzanine.pages.models import Page
from django.contrib.auth import models as auth
from django.conf.urls import url

class AbstractPageResource(ModelResource):
    """Abstract class that provides sensible defaults for creating new pages via the RESTful API. e.g. unless there's
     some specific value passed in for whether or not the page should show up in the header, footer, and sidebar, we
     want to dehydrate that field specifically"""

    def _dehydrate_with_default(self, bundle, datum, default):
        if datum not in bundle.data or bundle.data[datum] is None:
            return default

    def dehydrate_in_menus(self, bundle):
        return self._dehydrate_with_default(bundle, 'in_menus', False)

    def dehydrate_requires_login(self, bundle):
        return self._dehydrate_with_default(bundle, 'requires_login', False)

    def dehydrate_in_sitemap(self, bundle):
        return self._dehydrate_with_default(bundle, 'in_sitemap', False)


class BaseMeta(object):
    allowed_methods = ['get', 'put', 'post', 'delete']
    authorization = Authorization()
    authentication = SessionAuthentication()
    filtering = { 'slug' : ALL, 'title' : ALL, 'parent' : ALL_WITH_RELATIONS }


class Group(ModelResource):
    class Meta:
        authorization = Authorization()
        authentication = SessionAuthentication()
        allowed_methods = ['get']
        queryset = auth.Group.objects.all()
        resource_name = "group"


class User(ModelResource):
    class Meta:
        authorization = Authorization()
        authentication = SessionAuthentication()
        allowed_methods = ['get']
        queryset = auth.User.objects.all()
        resource_name = "user"


class CatalogPage(AbstractPageResource):
    class Meta:
        queryset = models.CatalogPage.objects.all()
        resource_name = 'catalog'
        allowed_methods = ['get']
        detail_uri_name = "slug"
    
    def prepend_urls(self):
        return [
            url(r"^(?P<resource_name>%s)/(?P<slug>[\w\d_.-]+)/$" % self._meta.resource_name, self.wrap_view('dispatch_detail'), name="api_dispatch_detail"),
        ]

class RelatedResource(AbstractPageResource):
    class Meta(BaseMeta):
        authorization = Authorization()
        authentication = SessionAuthentication()
        queryset = models.RelatedResource.objects.all()
        resource_name = "related"
        detail_uri_name = "slug"
    
    def prepend_urls(self):
        return [
            url(r"^(?P<resource_name>%s)/(?P<slug>[\w\d_.-]+)/$" % self._meta.resource_name, self.wrap_view('dispatch_detail'), name="api_dispatch_detail"),
        ]

class Page(AbstractPageResource):
   class Meta:
        queryset = Page.objects.all()
        resource_name = 'page'
        allowed_methods = ['get']
        detail_uri_name = "slug"
    
   def prepend_urls(self):
        return [
            url(r"^(?P<resource_name>%s)/(?P<slug>[\w\d_.-]+)/$" % self._meta.resource_name, self.wrap_view('dispatch_detail'), name="api_dispatch_detail"),
        ]
 

class DataResource(AbstractPageResource):
    parent = ForeignKey(CatalogPage, 'parent', full=False, null=True, blank=True, readonly=False)

    class Meta(BaseMeta):
        queryset = models.DataResource.objects.all()
        resource_name = 'data'
        fields = ['title','status','content','resource_file','resource_url','resource_irods_file','kind','driver','parent']
        detail_uri_name = "slug"
    
    def prepend_urls(self):
        return [
            url(r"^(?P<resource_name>%s)/(?P<slug>[\w\d_.-]+)/$" % self._meta.resource_name, self.wrap_view('dispatch_detail'), name="api_dispatch_detail"),
        ]


class ResourceGroup(AbstractPageResource):
    class Meta(BaseMeta):
        queryset = models.ResourceGroup.objects.all()
        resource_name = "resource_group"
        detail_uri_name = "slug"
    
    def prepend_urls(self):
        return [
            url(r"^(?P<resource_name>%s)/(?P<slug>[\w\d_.-]+)/$" % self._meta.resource_name, self.wrap_view('dispatch_detail'), name="api_dispatch_detail"),
        ]

resources = Api()
resources.register(User())
resources.register(Group())
resources.register(RelatedResource())
resources.register(DataResource())
resources.register(ResourceGroup())
resources.register(CatalogPage())


class Style(AbstractPageResource):
    parent = ForeignKey(CatalogPage, 'parent', full=False, null=True, blank=True, readonly=False)
    class Meta(BaseMeta):
        queryset = models.Style.objects.all()
        resource_name = "style"
        detail_uri_name = "slug"
    
    def prepend_urls(self):
        return [
            url(r"^(?P<resource_name>%s)/(?P<slug>[\w\d_.-]+)/$" % self._meta.resource_name, self.wrap_view('dispatch_detail'), name="api_dispatch_detail"),
        ]

styles = Api()
styles.register(Style())


class RenderedLayer(AbstractPageResource):
    data_resource = ForeignKey(DataResource, 'data_resource')
    default_style = ForeignKey(Style, 'default_style', related_name='default_for_layer')
    styles = ManyToManyField(Style, 'styles')
    parent = ForeignKey(CatalogPage, 'parent', full=False, null=True, blank=True, readonly=False)

    class Meta(BaseMeta):
        queryset = models.RenderedLayer.objects.all()
        resource_name = 'rendered_layer'
        detail_uri_name = "slug"
    
    def prepend_urls(self):
        return [
            url(r"^(?P<resource_name>%s)/(?P<slug>[\w\d_.-]+)/$" % self._meta.resource_name, self.wrap_view('dispatch_detail'), name="api_dispatch_detail"),
        ]


layers = Api()
layers.register(RenderedLayer())
