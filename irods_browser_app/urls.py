from django.conf.urls import patterns, url
from irods_browser_app import views

urlpatterns = patterns('',
    url(r'^login/$',views.login, name='irods_login'),
    url(r'^store/$',views.store, name='irods_store'),
    url(r'^upload/$',views.upload, name='irods_upload'),
 )
