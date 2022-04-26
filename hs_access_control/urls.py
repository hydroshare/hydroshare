from django.conf.urls import url
from hs_access_control import views

urlpatterns = [
    # Community responders
    # url(r'^_internal/community/(?P<cid>[0-9]+)/$',
    #     views.CommunityJsonView.as_view()),
    # url(r'^_internal/community/(?P<cid>[0-9]+)/(?P<action>[a-z_ ]*)/(?P<gid>[0-9]+)/$',
    #     views.CommunityJsonView.as_view()),

    # Community JSON responders
    url(r'^_internal/communityjson/(?P<cid>[0-9]+)/$',
        views.CommunityJsonView.as_view()),
    url(r'^_internal/communityjson/(?P<cid>[0-9]+)/(?P<action>[a-z_ ]*)/(?P<gid>[0-9]+)/$',
        views.CommunityJsonView.as_view()),

    # Group responders
    # url(r'^_internal/group/(?P<gid>[0-9]+)/$',
    #     views.GroupView.as_view()),
    # url(r'^_internal/group/(?P<gid>[0-9]+)/(?P<action>[a-z_ ]*)/(?P<cid>[0-9]+)/$',
    #     views.GroupView.as_view()),

    # # Group JSON responders
    url(r'^_internal/groupjson/(?P<gid>[0-9]+)/$',
        views.GroupJsonView.as_view()),
    url(r'^_internal/groupjson/(?P<gid>[0-9]+)/(?P<action>[a-z_ ]*)/(?P<cid>[0-9]+)/$',
        views.GroupJsonView.as_view()),

    # tests
    # url(r'^test/community/(?P<cid>[0-9]+)/$',
    #     views.TestCommunity.as_view()),
    # url(r'^test/group/(?P<gid>[0-9]+)/$',
    #     views.TestGroup.as_view()),
]
