from django.conf.urls import url
from hs_app_netCDF import views

urlpatterns = [
    url(
        r'^_internal/netcdf_update/(?P<resource_id>[A-z0-9\-_]+)/$',
        views.update_netcdf_file,
        name="update_netcdf_resfile")
]
