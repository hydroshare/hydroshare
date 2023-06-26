from django.conf.urls import url
from hs_access_control import views

urlpatterns = [
    # Community responders return JSON
    url(r'^_internal/community/(?P<cid>[0-9]+)/(?P<action>[a-z]+)/(?P<gid>[0-9]+)/$',
        views.CommunityView.as_view(), name='access_manage_community'),
    url(r'^_internal/community/(?P<cid>[0-9]+)/(?P<action>owner)/(?P<uid>[a-zA-Z0-9]+)/(?P<addrem>add|remove)$',
        views.CommunityView.as_view(), name='access_manage_community'),
    url(r'^_internal/community/(?P<cid>[0-9]+)/(?P<action>[a-z]+)/',
        views.CommunityView.as_view(), name='access_manage_community'),

    # Group responders return JSON
    url(r'^_internal/group/(?P<gid>[0-9]+)/$',
        views.GroupView.as_view(), name='access_manage_group'),
    url(r'^_internal/group/(?P<gid>[0-9]+)/(?P<action>[a-z_ ]*)/(?P<cid>[0-9]+)/$',
        views.GroupView.as_view(), name='access_manage_group'),

    # Community request responders also return JSON
    url(r'^_internal/crequest/$',
        views.CommunityRequestView.as_view(), name='access_manage_crequests'),
    url(r'^_internal/crequest/(?P<action>[a-z_]+)/$',
        views.CommunityRequestView.as_view(), name='access_manage_crequests'),
    url(r'^_internal/crequest/(?P<action>[a-z_]+)/(?P<crid>[0-9]+)/$',
        views.CommunityRequestView.as_view(), name='access_manage_crequests'),
]
