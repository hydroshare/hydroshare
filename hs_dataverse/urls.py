from django.urls import path
from . import views

urlpatterns = [
    # internal API
    # url(r'^_internal/(?P<shortkey>[0-9a-f-]+)/add-files-to-resource/$',
    #     views.add_files_to_resource, name='add_files_to_resource'),
    path('', views.datatest, name='datatest'),
]
