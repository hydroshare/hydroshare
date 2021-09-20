from django.conf.urls import include, url
from hs_community_mgmt import views

urlpatterns = [
    url(r'^cmgmt/$', views.TestView.as_view()),
    url(r'^_internal/gdata/(?P<gid>[0-9]+)/', views.get_group_info, name='gdata'),
    url(r'^_internal/owned_groups/(?P<uid>[0-9]+)/', views.user_owned_groups, name='get_owned_groups'),
    url(r'^_internal/owned_communities/(?P<uid>[0-9]+)/', views.user_owned_communities, name='get_owned_communities'),
    url(r'^_internal/pending_communities/(?P<uid>[0-9]+)/(?P<cid>[0-9]+)/', 
        views.user_community_pending, name='user_community_pending'),
    
    url(r'^_internal/uowned_resources/(?P<uid>[0-9]+)/', views.UserView.as_view()),
    
    url(r'^_internal/gowned_resources/(?P<uid>[0-9]+)/(?P<gid>[0-9]+)/', views.GroupView.as_view()),
    url(r'^_internal/cowned_resources/(?P<uid>[0-9]+)/(?P<gid>[0-9]+)/(?P<action>approve)/(?P<nuid>[0-9]+)/', views.GroupView.as_view()),
    url(r'^_internal/cowned_resources/(?P<uid>[0-9]+)/(?P<gid>[0-9]+)/(?P<action>decline)/(?P<nuid>[0-9]+)/', views.GroupView.as_view()),
    url(r'^_internal/cowned_resources/(?P<uid>[0-9]+)/(?P<gid>[0-9]+)/(?P<action>invite_user)/(?P<nuid>[0-9]+)/', views.GroupView.as_view()), 
    
    url(r'^_internal/cowned_resources/(?P<uid>[0-9]+)/(?P<cid>[0-9]+)/(?P<action>approve)/(?P<gid>[0-9]+)/', views.CommunityView.as_view()),
    url(r'^_internal/cowned_resources/(?P<uid>[0-9]+)/(?P<cid>[0-9]+)/(?P<action>decline)/(?P<gid>[0-9]+)/', views.CommunityView.as_view()),
    url(r'^_internal/cowned_resources/(?P<uid>[0-9]+)/(?P<cid>[0-9]+)/(?P<action>cancel)/(?P<gid>[0-9]+)/', views.CommunityView.as_view()),
    url(r'^_internal/cowned_resources/(?P<uid>[0-9]+)/(?P<cid>[0-9]+)/(?P<action>delete)/(?P<gid>[0-9]+)/', views.CommunityView.as_view()),
    url(r'^_internal/cowned_resources/(?P<uid>[0-9]+)/(?P<cid>[0-9]+)/(?P<action>remove_group)/(?P<gid>[0-9]+)/', views.CommunityView.as_view()),
    url(r'^_internal/cowned_resources/(?P<uid>[0-9]+)/(?P<cid>[0-9]+)/(?P<action>invite_group)/(?P<gid>[0-9]+)/', views.CommunityView.as_view()),
    url(r'^_internal/cowned_resources/(?P<uid>[0-9]+)/(?P<cid>[0-9]+)/(?P<gid>[0-9]+)/(?P<action>invite_group)/', views.CommunityView.as_view()),
    url(r'^_internal/cowned_resources/(?P<uid>[0-9]+)/(?P<cid>[0-9]+)/(?P<action>change_user)/', views.CommunityView.as_view()),
    url(r'^_internal/cowned_resources/(?P<uid>[0-9]+)/(?P<cid>[0-9]+)/', views.CommunityView.as_view()),

    url(r'^_internal/learning/(?P<uid>[0-9]+)/(?P<cid>[0-9]+)/(?P<action>approve)/(?P<gid>[0-9]+)/', views.LearnView.as_view()),
    url(r'^_internal/learning/(?P<uid>[0-9]+)/(?P<cid>[0-9]+)/(?P<action>decline)/(?P<gid>[0-9]+)/', views.LearnView.as_view()),
    url(r'^_internal/learning/(?P<uid>[0-9]+)/(?P<cid>[0-9]+)/(?P<action>cancel)/(?P<gid>[0-9]+)/', views.LearnView.as_view()),
    url(r'^_internal/learning/(?P<uid>[0-9]+)/(?P<cid>[0-9]+)/(?P<action>delete)/(?P<gid>[0-9]+)/', views.LearnView.as_view()),
    url(r'^_internal/learning/(?P<uid>[0-9]+)/(?P<cid>[0-9]+)/(?P<action>remove_group)/(?P<gid>[0-9]+)/', views.LearnView.as_view()),
    url(r'^_internal/learning/(?P<uid>[0-9]+)/(?P<cid>[0-9]+)/(?P<gid>[0-9]+)/(?P<action>invite_group)/', views.LearnView.as_view()),
    url(r'^_internal/learning/(?P<uid>[0-9]+)/(?P<cid>[0-9]+)/(?P<action>change_user)/', views.LearnView.as_view()),
    url(r'^_internal/learning/(?P<uid>[0-9]+)/(?P<cid>[0-9]+)/', views.LearnView.as_view()),
    
    url(r'^_internal/request/requests/(?P<uid>[0-9]+)/(?P<cid>[0-9]+)/', views.RequestView.Requests.as_view()),
    url(r'^_internal/request/requests/(?P<uid>[0-9]+)/(?P<cid>[0-9]+)/(?P<action>approve)/(?P<gid>[0-9]+)/', views.RequestView.Requests.as_view()),
    url(r'^_internal/request/requests/(?P<uid>[0-9]+)/(?P<cid>[0-9]+)/(?P<action>decline)/(?P<gid>[0-9]+)/', views.RequestView.Requests.as_view()),

    url(r'^_internal/request/debugging/(?P<uid>[0-9]+)/(?P<cid>[0-9]+)/', views.RequestView.Debugging.as_view()),    
    url(r'^_internal/request/redeemed/(?P<uid>[0-9]+)/(?P<cid>[0-9]+)/', views.RequestView.Redeemed.as_view()),
    url(r'^_internal/request/redeemed/(?P<uid>[0-9]+)/(?P<cid>[0-9]+)/(?P<action>delete)/(?P<gid>[0-9]+)/', views.RequestView.Redeemed.as_view()),
    url(r'^_internal/request/denied/(?P<uid>[0-9]+)/(?P<cid>[0-9]+)/', views.RequestView.Denied.as_view()),
    url(r'^_internal/request/denied/(?P<uid>[0-9]+)/(?P<cid>[0-9]+)/(?P<action>delete)/(?P<gid>[0-9]+)/', views.RequestView.Denied.as_view()),

    url(r'^_internal/request/invitations/(?P<uid>[0-9]+)/(?P<cid>[0-9]+)/', views.RequestView.Invitations.as_view()),
    url(r'^_internal/request/invitations/(?P<uid>[0-9]+)/(?P<cid>[0-9]+)/(?P<action>cancel)/(?P<gid>[0-9]+)/', views.RequestView.Invitations.as_view()),
    url(r'^_internal/request/comm_report/(?P<uid>[0-9]+)/(?P<cid>[0-9]+)/', views.RequestView.ReportView.as_view()),
    url(r'^_internal/request/comm_report/(?P<uid>[0-9]+)/(?P<cid>[0-9]+)/(?P<action>remove_group)/(?P<gid>[0-9]+)/', views.RequestView.ReportView.as_view()),
    

    url(r'^_internal/request/functions/', views.RequestView.Functions.as_view()),
    

    url(r'^_internal/umgmt/(?P<uid>[0-9]+)/', views.CommandView.as_view()),
    url(r'^_internal/learning/(?P<cid>[0-9]+)/', views.get_community_info, name='learning'),
    url(r'^_internal/get_user_info/(?P<uid>[0-9]+)/', views.get_user_info, name='get_user_info'),
    url(r'^_internal/get_group_info/(?P<gid>[0-9]+)/', views.get_group_info, name='get_group_info'),
    url(r'^_internal/accept_community_request/(?P<gid>[0-9]+)/(?P<uid>[0-9]+)/(?P<cid>[0-9]+)/', views.accept_community_request, name='accept_community_request'),
    url(r'^_internal/load_utable_data/(?P<uid>[0-9]+)/', views.load_utable_data, name='load_utable_data'),
]
