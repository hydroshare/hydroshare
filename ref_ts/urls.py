from django.conf.urls import patterns, url
from ref_ts import views

urlpatterns = patterns('',
    url(r'^_internal/create-ref-time-series/$', views.create_ref_time_series),
    url(r'^_internal/search-sites/$', views.search_sites),
    url(r'^_internal/search-variables/$', views.search_variables),
    url(r'^_internal/verify-rest-url/$', views.verify_rest_url),
    url(r'^_internal/time-series-from-service/$', views.time_series_from_service),
    url(r'^_internal/(?P<shortkey>[A-z0-9]+)/generate-files/$', views.generate_files),
    url(r'^_internal/(?P<shortkey>[A-z0-9]+)/transform-file/$', views.transform_file),
    url(r'^_internal/(?P<shortkey>[A-z0-9]+)/get-vis-link/$', views.get_vis_link)
    )