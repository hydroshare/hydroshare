import datetime
from logging import getLogger
import json

from django.contrib.auth.models import User, Group
from django.db.models.signals import post_save
from django.contrib.gis.db import models
from django.utils.timezone import utc
from mezzanine.pages.models import Page
from mezzanine.core.models import RichText
from mezzanine.conf import settings as s
from mezzanine.pages.page_processors import processor_for
from timedelta.fields import TimedeltaField
import sh
import os
from osgeo import osr
import importlib


_log = getLogger('ga_resources')

def get_user(request):
    from tastypie.models import ApiKey
    """authorize user based on API key if it was passed, otherwise just use the request's user.

    :param request:
    :return: django.contrib.auth.User
    """
    if 'api_key' in request.REQUEST:
        api_key = ApiKey.objects.get(key=request.REQUEST['api_key'])
        return api_key.user
    elif request.user.is_authenticated():
        return User.objects.get(pk=request.user.pk)
    else:
        return request.user

class PagePermissionsMixin(object):
    def storage_key(self, kfor):
        return "{label}.{model}.{key}.{kfor}".format(
            label=self._meta.app_label,
            model=self._meta.module_name,
            key=self.pk,
            kfor=kfor
        )

    @property
    def permissions_store(self):
        return s.PERMISSIONS_DB

    @property
    def edit_users(self):
        return set(self.permissions_store.smembers(self.storage_key('edit-users')))

    @property
    def edit_groups(self):
        return set(self.permissions_store.smembers(self.storage_key('edit-groups')))

    @property
    def view_users(self):
        return set(self.permissions_store.smembers(self.storage_key('view-users')))

    @property
    def view_groups(self):
        return set(self.permissions_store.smembers(self.storage_key('view-groups')))


    def add_edit_user(self, user):
        self.permissions_store.sadd(self.storage_key('edit-users'), user if isinstance(user, int) else user.pk)


    def add_view_user(self, user):
        self.permissions_store.sadd(self.storage_key('view-users'), user if isinstance(user, int) else user.pk)


    def add_edit_group(self, group):
        self.permissions_store.sadd(self.storage_key('edit-groups'), group if isinstance(group, int) else group.pk)


    def add_view_group(self, group):
        self.permissions_store.sadd(self.storage_key('view-groups'), group if isinstance(group, int) else group.pk)


    def remove_edit_user(self, user):
        self.permissions_store.srem(self.storage_key('edit-users'), user if isinstance(user, int) else user.pk)


    def remove_view_user(self, user):
        self.permissions_store.srem(self.storage_key('view-users'), user if isinstance(user, int) else user.pk)


    def remove_edit_group(self, group):
        self.permissions_store.srem(self.storage_key('edit-groups'), group if isinstance(group, int) else group.pk)


    def remove_view_group(self, group):
        self.permissions_store.srem(self.storage_key('view-groups'), group if isinstance(group, int) else group.pk)

    def can_add(self, request):
        return self.can_change(request)

    def can_delete(self, request):
        return self.can_change(request)


    def can_change(self, request):
        user = get_user(request)

        ret = True

        if user.is_authenticated():
            if not self.owner:
                ret = user.is_superuser
            elif user.pk == self.owner.pk:
                ret = True
            else:
                users = self.edit_users
                groups = self.edit_groups

                if len(users) > 0 and user.pk in users:
                    ret = True
                elif len(groups) > 0:
                    ret = user.groups.filter(pk__in=groups).exists()
                else:
                    ret =  False
        else:
            ret = False

        return ret


    def can_view(self, request):
        user = get_user(request)

        if self.public or not self.owner:
            return True
        if user.is_authenticated():
            if not self.owner:
                return user.is_superuser
            elif user.pk == self.owner.pk:
                return True
            else:
                users = self.view_users
                groups = self.view_groups

                if len(users) > 0 and user.pk in users:
                    return True
                elif len(groups) > 0:
                    return user.groups.filter(pk__in=groups).exists()
                else:
                    return False
        else:
            return False

    def copy_permissions_to_children(self, clear_existing=True, recurse=False):
        # pedantically implemented.  should use set logic to minimize changes, but ptobably not important
        for child in self.children:
            if isinstance(child, PagePermissionsMixin):
                if clear_existing:
                    for u in child.edit_users:
                        child.remove_edit_user(u)
                    for u in child.view_users:
                        child.remove_view_user(u)
                    for g in child.edit_groups:
                        child.remove_edit_group(g)
                    for g in child.view_groups:
                        child.remove_view_group(g)

                for u in self.edit_users:
                    child.add_edit_user(u)
                for u in self.view_users:
                    child.add_view_user(u)
                for g in self.edit_groups:
                    child.add_edit_group(g)
                for g in self.view_groups:
                    child.add_view_group(g)

                child.public = self.public
                child.owner = self.owner
                child.save()
                    
                if recurse:
                    child.copy_permissions_to_children(clear_existing=clear_existing, recurse=recurse)


    def copy_permissions_from_parent(self, clear_existing=True):
        parent = self.parent.get_content_model()
        if isinstance(parent, PagePermissionsMixin):
            if clear_existing:
                for u in self.edit_users:
                    self.remove_edit_user(u)
                for u in self.view_users:
                    self.remove_view_user(u)
                for g in self.edit_groups:
                    self.remove_edit_group(g)
                for g in self.view_groups:
                    self.remove_view_group(g)

            for u in self.parent.edit_users:
                self.add_edit_user(u)
            for u in self.parent.view_users:
                self.add_view_user(u)
            for g in self.parent.edit_groups:
                self.add_edit_group(g)
            for g in self.parent.view_groups:
                self.add_view_group(g)

            self.public = self.parent.public
            self.owner = self.parent.owner
            self.save()


# this should be used as the page processor for anything with pagepermissionsmixin
# page_processor_for(MyPage)(ga_resources.views.page_permissions_page_processor)
def page_permissions_page_processor(request, page):
    page = page.get_content_model()
    edit_groups = Group.objects.filter(pk__in=page.edit_groups)
    view_groups = Group.objects.filter(pk__in=page.view_groups)
    edit_users = User.objects.filter(pk__in=page.edit_users)
    view_users = User.objects.filter(pk__in=page.view_users)

    return {
        "edit_groups": edit_groups,
        "view_groups": view_groups,
        "edit_users": edit_users,
        "view_users": view_users,
    }


class CatalogPage(Page, PagePermissionsMixin):
    """Maintains an ordered catalog of data.  These pages are rendered specially but otherwise are not special."""

    public = models.BooleanField(default=True)
    owner = models.ForeignKey(User, null=True)

    class Meta:
        ordering = ['title']

    @property
    def siblings(self):
        if self.parent:
            return set(self.parent.children.all()) - {self}
        else:
            return set()

    @classmethod
    def ensure_page(cls, *titles, **kwargs):
        parent = kwargs.get('parent', None)
        child = kwargs.get('child', None)
        if child:
            del kwargs['child']
        if parent:
            del kwargs['parent']

        if not cls.objects.filter(title=titles[0], parent=parent).exists():
            p = cls.objects.create(title=titles[0], parent=parent, **kwargs)
        else:
            p = cls.objects.get(title=titles[0], parent=parent)

        for title in titles[1:]:
            if not cls.objects.filter(title=title, parent=p).exists():
                p = cls.objects.create(title=title, parent=p, **kwargs)
            else:
                p = cls.objects.get(title=title, parent=p)

        if child:
            child.parent = p
            child.save()

        return p

    def save(self, *args, **kwargs):
        return super(CatalogPage, self).save(*args, **kwargs)

def set_permissions_for_new_catalog_page(sender, instance, created, *args, **kwargs):
    if instance.parent and created:
        instance.copy_permissions_from_parent()

@processor_for(CatalogPage)
def catalog_page_processor(request, page):
    viewable_children = []
    viewable_siblings = []
    for child in page.children.all():
        if not hasattr(page, 'can_view') or page.can_view(request):
            viewable_children.append(child)

    if page.parent:
        for child in page.parent.children.exclude(slug=page.slug):
            if not hasattr(page, 'can_view') or page.can_view(request):
                viewable_siblings.append(child)

    ctx = page_permissions_page_processor(request, page)
    ctx['viewable_children'] = viewable_children
    ctx['viewable_siblings'] = viewable_siblings

    return ctx

set_permissions = post_save.connect(set_permissions_for_new_catalog_page, sender=CatalogPage, weak=False)


class DataResource(Page, RichText, PagePermissionsMixin):
    """Represents a file that has been uploaded to Geoanalytics for representation"""
    resource_file = models.FileField(upload_to='ga_resources', null=True, blank=True)
    resource_url = models.URLField(null=True, blank=True)
    resource_config = models.TextField(null=True, blank=True)
    last_change = models.DateTimeField(null=True, blank=True)
    last_refresh = models.DateTimeField(null=True, blank=True) # updates happen only to resources that were not uploaded by the user.
    next_refresh = models.DateTimeField(null=True, blank=True, db_index=True) # will be populated every time the update manager runs
    refresh_every = TimedeltaField(null=True, blank=True)
    md5sum = models.CharField(max_length=64, blank=True, null=True) # the unique md5 sum of the data
    metadata_url = models.URLField(null=True, blank=True)
    metadata_xml = models.TextField(null=True, blank=True)
    native_bounding_box = models.PolygonField(null=True, blank=True)
    bounding_box = models.PolygonField(null=True, srid=4326, blank=True)
    three_d = models.BooleanField(default=False)
    native_srs = models.TextField(null=True, blank=True)
    public = models.BooleanField(default=True)
    owner = models.ForeignKey(User, null=True)

    driver = models.CharField(
        default='ga_resources.drivers.spatialite',
        max_length=255,
        null=False,
        blank=False,
        choices=getattr(s, 'INSTALLED_DATARESOURCE_DRIVERS', (
            ('ga_resources.drivers.spatialite', 'Spatialite (universal)'),
            ('ga_resources.drivers.shapefile', 'Shapefile'),
            ('ga_resources.drivers.geotiff', 'GeoTIFF'),
            ('ga_resources.drivers.postgis', 'PostGIS'),
            ('ga_resources.drivers.kmz', 'Google Earth KMZ'),
            ('ga_resources.drivers.ogr', 'OGR DataSource'),
        )))
    big = models.BooleanField(default=False, help_text='Set this to be true if the dataset is more than 100MB') # causes certain drivers to optimize for datasets larger than memory

    class Meta:
        ordering = ['title']

    @property
    def srs(self):
        if not self.native_srs:
            self.driver_instance.compute_fields()
        srs = osr.SpatialReference()
        srs.ImportFromProj4(self.native_srs.encode('ascii'))
        return srs

    @property
    def dataframe(self):
        return self.driver_instance.as_dataframe()

    @property
    def driver_instance(self):
        """deprecated"""
        if not hasattr(self, '_driver_instance'):
            self._driver_instance = importlib.import_module(self.driver).driver(self)
        return self._driver_instance

    @property
    def resource(self):
        return self.driver_instance

    def modified(self):
        self.last_refresh = datetime.datetime.utcnow().replace(tzinfo=utc)
        self.driver_instance.clear_cache()
        
    @property
    def cache_path(self):
        p = os.path.join(s.MEDIA_ROOT, ".cache", "resources", *os.path.split(self.slug))
        if not os.path.exists(p):
            os.makedirs(p)  # just in case it's not there yet.
        return p

    @property
    def driver_config(self):
        return json.loads(self.resource_config) if self.resource_config else {}


        

class OrderedResource(models.Model):
    resource_group = models.ForeignKey("ResourceGroup")
    data_resource = models.ForeignKey(DataResource)
    ordering = models.IntegerField(default=0)

class ResourceGroup(Page):
    """Represents a group of resources, which is possibly a time series"""
    resources = models.ManyToManyField(DataResource, blank=True, through=OrderedResource)
    is_timeseries = models.BooleanField(default=False)
    min_time = models.DateTimeField(null=True)
    max_time = models.DateTimeField(null=True)

class RelatedResource(Page, RichText):
    """Represents a file that can be joined onto a vector resource"""
    UPPERCASE = 0
    CAPITALIZE = 1
    LOWERCASE = 2

    resource_file = models.FileField(upload_to='ga_resources')
    foreign_resource = models.ForeignKey(DataResource)
    foreign_key = models.CharField(max_length=64, blank=True, null=True)
    local_key = models.CharField(max_length=64, blank=True, null=True)
    left_index = models.BooleanField(default=False)
    right_index = models.BooleanField(default=False)
    how = models.CharField(max_length=8, default='left', choices=(
        ('left','left'),
        ('right','right'),
        ('outer','outer'),
        ('inner','inner'),
    ))
    driver = models.CharField(max_length=255,default='ga_resources.drivers.related.excel')
    key_transform = models.IntegerField(blank=True, null=True, choices=(
        (CAPITALIZE, "Capitalize"),
        (LOWERCASE, "Lower case"),
        (UPPERCASE, "Upper case")
    ))

    @property
    def driver_instance(self):
        if not hasattr(self, '_driver_instance'):
            self._driver_instance = importlib.import_module(self.driver).driver(self)
        return self._driver_instance

    @property
    def cache_path(self):
        p = os.path.join(s.MEDIA_ROOT, ".cache", "resources", *os.path.split(self.slug))
        if not os.path.exists(p):
            os.makedirs(p)  # just in case it's not there yet.
        return p

class Style(Page, PagePermissionsMixin):
    """A stylesheet in CartoCSS format."""
    legend = models.ImageField(upload_to='ga_resources.styles.legends', width_field='legend_width', height_field='legend_height', null=True, blank=True)
    legend_width = models.IntegerField(null=True, blank=True)
    legend_height = models.IntegerField(null=True, blank=True)
    stylesheet = models.TextField()
    public = models.BooleanField(default=True)
    owner = models.ForeignKey(User, null=True)

    def modified(self):
        if s.WMS_CACHE_DB.exists(self.slug):
            cached_filenames = s.WMS_CACHE_DB.smembers(self.slug)
            for filename in cached_filenames:
                sh.rm('-rf', sh.glob(filename+"*"))
            s.WMS_CACHE_DB.srem(self.slug, cached_filenames)


class RenderedLayer(Page, RichText, PagePermissionsMixin):
    """All the general stuff for a layer.  Layers inherit ownership and group info from the data resource"""
    data_resource = models.ForeignKey(DataResource)
    default_style = models.ForeignKey(Style, related_name='default_for_layer')
    default_class = models.CharField(max_length=255, default='default')
    styles = models.ManyToManyField(Style)
    public = models.BooleanField(default=True)
    owner = models.ForeignKey(User, null=True)
