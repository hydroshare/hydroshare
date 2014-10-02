from django.conf.urls import patterns, include, url
from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin
from django.views.generic import ListView, UpdateView,TemplateView

from . import  views, models
from .views.organization import OrganizationDetail,OrganizationList,OrganizationEdit,OrganizationCreate
from .views.person import PersonEdit,PersonDetail, PersonList,PersonCreate
from .views.organizationassociation import OrganizationAssociationCreate,OrganizationAssociationEdit,OrganizationAssociationDetail
from . import api

__author__ = 'valentin'

urlpatterns = i18n_patterns('hs_party.api',

        url(r'^api/', include(api.party_v1_api.urls) ),
        # bad pattern r'^papi/$'
        # #url(r'^papi/$', include(api.party_v1_api.urls) ),
)

urlpatterns += patterns('hs_party.views.organization',

      url(r'^organization/add/$', OrganizationCreate.as_view(), name="organization_add"),
      url(r'^organization/(?P<pk>\d+)/$', OrganizationDetail.as_view(), name="organization_detail"),
     url(r'^organization/(?P<pk>\d+)/edit/$', OrganizationEdit.as_view(template_name='pages/orgs/organization_edit.html',),
        name="organization_edit"),
         url(r'^organization/', OrganizationList.as_view(), name="organization_list"),
    )

urlpatterns += patterns('hs_party.views.person',

        url(r'^person/add/$', PersonCreate.as_view(), name="person_add"),
        url(r'^person/(?P<pk>\d+)/$', PersonDetail.as_view(template_name = "pages/person/person.html",), name="person_detail"),
        url(r'^person/(?P<pk>\d+)/edit/$', PersonEdit.as_view(template_name = "pages/person/person_edit.html"), name="person_edit"),
        url(r'^person/', PersonList.as_view( template_name = "pages/person/person_list.html"), name="person_list"),
   )

urlpatterns += patterns('hs_party.views.organizationassociation',

        url(r'^association/add/$', OrganizationAssociationCreate.as_view(), name="association_add"),
         url(r'^association/(?P<pk>\d+)/$', OrganizationAssociationDetail.as_view( template_name = "pages/associations/organization_association.html"), name="association_detail"),
        url(r'^association/(?P<pk>\d+)/edit/$', OrganizationAssociationEdit.as_view(template_name = "pages/associations/organization_association_edit.html"), name="association_edit"),
 )

urlpatterns += patterns('',

 url(r'^$', TemplateView.as_view(template_name='pages/index_party.html'), name="party_home"),
 )


