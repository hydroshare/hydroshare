from tastypie.api import Api,NamespacedApi
from tastypie import fields
from tastypie.contrib.contenttypes.fields import GenericForeignKeyField
from tastypie.authentication import BasicAuthentication, ApiKeyAuthentication, SessionAuthentication, MultiAuthentication
from tastypie.authorization import Authorization, DjangoAuthorization
from tastypie.resources import ModelResource
from tastypie.constants import ALL
from django.conf.urls import url

from .models.party import Party
from .models.person import Person
from .models.organization import Organization,OrganizationCodeList
from .models.organization_association import OrganizationAssociation

from .serializers.person import PersonFoafSerializer
from .serializers.organization import OrganizationFFoafSerializer
from .serializers.organization_association import OrganizationAssociationFoafSerializer

__author__ = 'valentin'

#party_v1_api = NamespacedApi(api_name='v1',urlconf_namespace='party')
party_v1_api = Api(api_name='v1')

class PersonResource(ModelResource):
    memberOf = fields.ToManyField('hs_party.api.OrganizationAssociationResource','organizationassociation_set')

    class Meta:
        queryset = Person.objects.all()
        resource_name = 'person'
        collection_name ='people'
        always_return_data = True
        #include_absolute_url = True #need to add get_absolute_url
        serializer=PersonFoafSerializer()
        # exclude displayable properties, and management dates
        excludes = ['createdDate', 'lastUpdate',
              'created','_meta_title','status','description',
              'expiry_date',   'gen_description',   'in_sitemap' ,
              'keywords_string','publish_date','slug','updated'
        ]
        #excludes = ['createdDate', 'lastUpdate']
        #filtering = {
        #    'name': ALL,
        #}
        #authentication = MultiAuthentication(BasicAuthentication(), ApiKeyAuthentication(), SessionAuthentication())
        # make it so only superusers and people with express permission can modify / create user objects
        #authorization = DjangoAuthorization()


    pass

party_v1_api.register(PersonResource())

class OrganizationResource(ModelResource):

    class Meta:
        resource_name = 'organization'
        queryset = Organization.objects.all()
        collection_name ='organizations' # without this name is object
        always_return_data = True
        #include_absolute_url = True #need to add get_absolute_url
        serializer=OrganizationFFoafSerializer()
        # exclude displayable properties, and management dates
        excludes = ['createdDate', 'lastUpdate',
              'created','_meta_title','status','description',
              'expiry_date',   'gen_description',   'in_sitemap' ,
              'keywords_string','publish_date','slug','updated'
        ]
        filtering = {
            'name': ALL,
        }

        #authentication = MultiAuthentication(BasicAuthentication(), ApiKeyAuthentication(), SessionAuthentication())
        # make it so only superusers and people with express permission can modify / create user objects
        #authorization = DjangoAuthorization()

    pass

party_v1_api.register(OrganizationResource())

class OrganizationAssociationResource(ModelResource):
    person = fields.ForeignKey(PersonResource,'person', full_detail=True)
    organization = fields.ForeignKey(OrganizationResource,'organization',full_detail=True)

    class Meta:
        queryset = OrganizationAssociation.objects.all()
        resource_name = 'organization_association'
        collection_name ='organization_associations' # without this name is object

        always_return_data = True
        #include_absolute_url = True #need to add get_absolute_url
        serializer=OrganizationAssociationFoafSerializer()
        # excludes = ['createdDate',
        #             ]
        # filtering = {
        #     'name': ALL,
        # }

        #authentication = MultiAuthentication(BasicAuthentication(), ApiKeyAuthentication(), SessionAuthentication())
        # make it so only superusers and people with express permission can modify / create user objects
        #authorization = DjangoAuthorization()

    pass


party_v1_api.register(OrganizationAssociationResource())

class OrganizationalCodeListResource(ModelResource):
    class Meta:
        always_return_data = True
        queryset = OrganizationCodeList.objects.all()
        resource_name = 'organization_type'
        collection_name = 'organization_types'
        filtering = {
            'name': ALL,
        }
        # exclude displayable properties, and management dates
        excludes = ['createdDate', 'lastUpdate',
              'created','_meta_title','status','description',
              'expiry_date',   'gen_description',   'in_sitemap' ,
              'keywords_string','publish_date','slug','updated'
        ]
        #authentication = MultiAuthentication(BasicAuthentication(), ApiKeyAuthentication(), SessionAuthentication())
        # make it so only superusers and people with express permission can modify / create group objects
        #authorization = DjangoAuthorization()

    # def prepend_urls(self):
    #     return [
    #         url(r"^(?P<resource_name>%s)/(?P<pk>[\w\d_.-]+)/$" % self._meta.resource_name, self.wrap_view('dispatch_detail'), name="api_dispatch_detail"),
    #     ]

party_v1_api.register(OrganizationalCodeListResource())