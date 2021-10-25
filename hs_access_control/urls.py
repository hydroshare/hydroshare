from django.conf.urls import url
from hs_access_control import views

urlpatterns = [
    # Community responders
    url(r'^_internal/community/(?P<uid>[0-9]+)/(?P<cid>[0-9]+)/$',
        views.CommunityView.as_view()),
    url(r'^_internal/community/(?P<uid>[0-9]+)/(?P<cid>[0-9]+)/(?P<action>[a-z_ ]*)/(?P<gid>[0-9]+)/$',
        views.CommunityView.as_view()),

    # Group responders
    url(r'^_internal/group/(?P<uid>[0-9]+)/(?P<gid>[0-9]+)/$',
        views.GroupView.as_view()),
    url(r'^_internal/group/(?P<uid>[0-9]+)/(?P<gid>[0-9]+)/(?P<action>[a-z_ ]*)/(?P<cid>[0-9]+)/$',
        views.GroupView.as_view()),

    # tests
    url(r'^test/community/(?P<uid>[0-9]+)/(?P<cid>[0-9]+)/$',
        views.TestCommunity.as_view()),
    url(r'^test/group/(?P<uid>[0-9]+)/(?P<gid>[0-9]+)/$',
        views.TestGroup.as_view()),
]
