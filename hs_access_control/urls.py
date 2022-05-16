from django.conf.urls import url
from hs_access_control import views

urlpatterns = [
    # Community responders
    url(r'^_internal/community/(?P<cid>[0-9]+)/$',
        views.CommunityView.as_view()),
    url(r'^_internal/community/(?P<cid>[0-9]+)/(?P<action>[a-z_ ]*)/(?P<gid>[0-9]+)/$',
        views.CommunityView.as_view()),

    # Community JSON responders
    url(r'^_internal/communityjson/(?P<cid>[0-9]+)/$',
        views.CommunityView.as_view()),
    url(r'^_internal/communityjson/(?P<cid>[0-9]+)/(?P<action>[a-z_ ]*)/(?P<gid>[0-9]+)/$',
        views.CommunityView.as_view()),

    # Group responders
    url(r'^_internal/group/(?P<gid>[0-9]+)/$',
        views.GroupView.as_view()),
    url(r'^_internal/group/(?P<gid>[0-9]+)/(?P<action>[a-z_ ]*)/(?P<cid>[0-9]+)/$',
        views.GroupView.as_view()),

    # # Group JSON responders
    url(r'^_internal/groupjson/(?P<gid>[0-9]+)/$',
        views.GroupView.as_view()),
    url(r'^_internal/groupjson/(?P<gid>[0-9]+)/(?P<action>[a-z_ ]*)/(?P<cid>[0-9]+)/$',
        views.GroupView.as_view()),
]
