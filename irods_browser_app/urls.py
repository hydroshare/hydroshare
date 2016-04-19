from django.conf.urls import patterns, url
from irods_browser_app import views

urlpatterns = patterns('',
    url(r'^login/$',views.login, name='irods_login'),
    url(r'^store/$',views.store, name='irods_store'),
    url(r'^store_uz/$',views.store_uz, name='irods_store_uz'),
    url(r'^upload/$',views.upload, name='irods_upload'),
    url(r'^upload_add/$',views.upload_add, name='irods_upload_add'),
 )
