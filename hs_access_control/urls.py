from django.conf.urls import url
from hs_access_control import views

urlpatterns = [
    url(r'^test/community/approval/(?P<uid>[0-9]+)/(?P<cid>[0-9]+)/$',
        views.TestCommunityApproval.as_view()),

    url(r'^test/group/approval/(?P<uid>[0-9]+)/(?P<gid>[0-9]+)/$',
        views.TestGroupApproval.as_view()),

    url(r'^test/debug/$', 
        views.DebugView.as_view()),

    url(r'^_internal/group/respond/(?P<uid>[0-9]+)/(?P<gid>[0-9]+)/$',
        views.GroupApprovalView.as_view()),
    url(r'^_internal/group/respond/(?P<uid>[0-9]+)/(?P<gid>[0-9]+)/(?P<action>[a-z_ ]*)/(?P<cid>[0-9]+)/$',
        views.GroupApprovalView.as_view()),

    url(r'^_internal/community/respond/(?P<uid>[0-9]+)/(?P<cid>[0-9]+)/$',
        views.CommunityApprovalView.as_view()),
    url(r'^_internal/community/respond/(?P<uid>[0-9]+)/(?P<cid>[0-9]+)/(?P<action>[a-z_ ]*)/(?P<gid>[0-9]+)/$',
        views.CommunityApprovalView.as_view()),

]
