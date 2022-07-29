from django.conf.urls import url
from hs_access_control import views

urlpatterns = [
    # Community responders return JSON
    url(r'^_internal/community/(?P<cid>[0-9]+)/$',
        views.CommunityView.as_view()),
    url(r'^_internal/community/(?P<cid>[0-9]+)/(?P<action>[a-z_ ]*)/(?P<gid>[0-9]+)/$',
        views.CommunityView.as_view()),

    # Community JSON responders (deprecated)
    # url(r'^_internal/communityjson/(?P<cid>[0-9]+)/$',
    #     views.CommunityView.as_view()),
    # url(r'^_internal/communityjson/(?P<cid>[0-9]+)/(?P<action>[a-z_ ]*)/(?P<gid>[0-9]+)/$',
    #     views.CommunityView.as_view()),

    # Group responders return JSON
    url(r'^_internal/group/(?P<gid>[0-9]+)/$',
        views.GroupView.as_view()),
    url(r'^_internal/group/(?P<gid>[0-9]+)/(?P<action>[a-z_ ]*)/(?P<cid>[0-9]+)/$',
        views.GroupView.as_view()),

    # Group JSON responders (deprecated)
    url(r'^_internal/groupjson/(?P<gid>[0-9]+)/$',
        views.GroupView.as_view()),
    url(r'^_internal/groupjson/(?P<gid>[0-9]+)/(?P<action>[a-z_ ]*)/(?P<cid>[0-9]+)/$',
        views.GroupView.as_view()),

    # Community request responders return JSON
    url(r'^_internal/crequest/$', views.CommunityRequestView.as_view()),
    url(r'^_internal/crequest/(?P<action>[a-z_]+)/(?P<crid>[0-9]+)/$',
        views.CommunityRequestView.as_view()),
]
