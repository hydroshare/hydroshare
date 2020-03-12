from django.conf.urls import url
from . import views

urlpatterns = [
    # internal API
    # url(r'^_internal/(?P<shortkey>[0-9a-f-]+)/add-files-to-resource/$',
    #     views.add_files_to_resource, name='add_files_to_resource'),
    url('^datatest$', views.datatest, name='datatest'),
]
