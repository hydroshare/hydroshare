from django.conf.urls import url
from hs_access_control import views

urlpatterns = [
    url(r'^test/(?P<uid>[0-9]+)/(?P<cid>[0-9]+)/$', views.TestView.as_view()),

    url(r'^_internal/group/respond/(?P<uid>[0-9]+)/(?P<gid>[0-9]+)/$', views.GroupView.as_view()),
    url(r'^_internal/group/respond/(?P<uid>[0-9]+)/(?P<gid>[0-9]+)/(?P<action>[a-z_ ]*)/(?P<nuid>[0-9]+)/$', views.GroupView.as_view()),

    url(r'^_internal/community/respond/(?P<uid>[0-9]+)/(?P<cid>[0-9]+)/$', views.CommunityView.as_view()),
    url(r'^_internal/community/respond/(?P<uid>[0-9]+)/(?P<cid>[0-9]+)/(?P<action>[a-z_ ]*)/(?P<gid>[0-9]+)/$', views.CommunityView.as_view()),

    url(r'^_internal/debug/(?P<uid>[0-9]+)/(?P<cid>[0-9]+)/', views.DebugView.as_view()), 
]
