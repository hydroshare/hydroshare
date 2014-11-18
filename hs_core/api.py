from __future__ import absolute_import
from django.conf.urls import url

from django.contrib.auth.models import User, Group

from tastypie.api import Api
from tastypie import fields
from tastypie.contrib.contenttypes.fields import GenericForeignKeyField
from tastypie.authentication import BasicAuthentication, ApiKeyAuthentication, SessionAuthentication, MultiAuthentication
from tastypie.authorization import Authorization, DjangoAuthorization
from tastypie.resources import ModelResource
from tastypie.constants import ALL

from hs_core.authorization import HydroshareAuthorization
from dublincore.models import QualifiedDublinCoreElement
from hs_core.models import GenericResource, ResourceFile

v1_api = Api(api_name='v1')

class UserResource(ModelResource):
    class Meta:
        always_return_data = True
        queryset = User.objects.all()
        resource_name = 'user'
        excludes = ['password', 'is_active', 'is_staff', 'is_superuser']
        filtering = {
            'username': ALL,
        }
        authentication = MultiAuthentication(BasicAuthentication(), ApiKeyAuthentication(), SessionAuthentication())
        # make it so only superusers and people with express permission can modify / create user objects
        authorization = DjangoAuthorization()
v1_api.register(UserResource())

class GroupResource(ModelResource):
    class Meta:
        always_return_data = True
        queryset = Group.objects.all()
        resource_name = 'group'
        excludes = ['password', 'is_active', 'is_staff', 'is_superuser']
        filtering = {
            'username': ALL,
        }
        authentication = MultiAuthentication(BasicAuthentication(), ApiKeyAuthentication(), SessionAuthentication())
        # make it so only superusers and people with express permission can modify / create group objects
        authorization = DjangoAuthorization()
v1_api.register(GroupResource())



class GenericResourceResource(ModelResource):
    user = fields.ForeignKey(UserResource, 'user')
    creator = fields.ForeignKey(UserResource, 'creator')
    edit_users = fields.OneToManyField(UserResource, 'edit_users', related_name='can_edit', blank=True)
    view_users = fields.OneToManyField(UserResource, 'edit_users', related_name='can_edit', blank=True)
    edit_groups = fields.OneToManyField(GroupResource, 'edit_users', related_name='can_edit', blank=True)
    view_groups = fields.OneToManyField(GroupResource, 'edit_users', related_name='can_edit', blank=True)
    owners = fields.OneToManyField(UserResource, 'owners', related_name='owner_of', blank=True)
    dublin_metadata = fields.ManyToManyField("hs_core.api.DublinCoreResource", 'dublin_metadata', related_name='content_object', full=True)
    files = fields.ManyToManyField('hs_core.api.ResourceFileResource', 'files', related_name='content_object', full=True)

    def prepend_urls(self):
        return [
            url(r"^(?P<resource_name>%s)/(?P<short_id>[\w\d_.-]+)/$" % self._meta.resource_name, self.wrap_view('dispatch_detail'), name="api_dispatch_detail"),
        ]

    class Meta:
        always_return_data = True
        queryset = GenericResource.objects.all()
        resource_name = 'genericresource'
        filtering = {
            'id': 'exact',
        }
        authentication = MultiAuthentication(BasicAuthentication(), ApiKeyAuthentication(), SessionAuthentication())
        #authorization = HydroshareAuthorization()
        authorization = Authorization()
v1_api.register(GenericResourceResource())

class DublinCoreResource(ModelResource):
    content_object = GenericForeignKeyField({
        GenericResource: GenericResourceResource
    }, 'content_object')

    class Meta:
        always_return_data = True
        queryset = QualifiedDublinCoreElement.objects.all()
        resource_name = 'dublincore'
        filtering = {
            'id': 'exact',
        }
        authentication = MultiAuthentication(BasicAuthentication(), ApiKeyAuthentication(), SessionAuthentication())
        #authorization = HydroshareAuthorization()
        authorization = Authorization()
v1_api.register(DublinCoreResource())

class ResourceFileResource(ModelResource):
    content_object = GenericForeignKeyField({
        GenericResource: GenericResourceResource
    }, 'content_object')

    class Meta:
        always_return_data = True
        queryset = ResourceFile.objects.all()
        resource_name = 'resource_file'
        filtering = {
            'id': 'exact',
        }
        authentication = MultiAuthentication(BasicAuthentication(), ApiKeyAuthentication(), SessionAuthentication())
        authorization = Authorization()
v1_api.register(ResourceFileResource())

