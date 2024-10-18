from django.urls import path

from irods_browser_app import views

urlpatterns = [
    path('login/', views.login, name='irods_login'),
    path('store/', views.store, name='irods_store'),
    path('upload_add/', views.upload_add, name='irods_upload_add'),
]
