from __future__ import unicode_literals

from django.conf.urls import patterns, include, url,\
    handler400, handler403, handler404, handler500
from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin
from django.views.generic import TemplateView

from mezzanine.conf import settings

import autocomplete_light

from hs_core.views.discovery_view import DiscoveryView
from hs_core.views.discovery_json_view import DiscoveryJsonView
from theme import views as theme
from hs_tracking import views as tracking
import hs_core.views as hs_core_views
from hs_app_timeseries import views as hs_ts_views
from hs_app_netCDF import views as nc_views


autocomplete_light.autodiscover()
admin.autodiscover()

urlpatterns = i18n_patterns("",
    url("^admin/", include(admin.site.urls)),
    url(r'^o/', include('oauth2_provider.urls', namespace='oauth2_provider')),

    # CMS Stuff
    url("^$", theme.HomePageView.as_view(), name="home"),
    url(r'^sitemap/$', 'hs_sitemap.views.sitemap', name='sitemap'),
    url(r'^comments/', include('django_comments.urls')),
    url(r'^rating/$', theme.rating),

    # XDCIShare Basics
    url( r'^r/(?P<shortkey>[A-z0-9\-_]+)', hs_core_views.short_url),
    url(r'^rn/(?P<short_id>[A-z0-9\-_]+)', hs_core_views.resource_frontend.resource_detail, name='resource_detail'),

    url(r'^search/$', hs_core_views.discovery_view.DiscoveryView.as_view(), name='haystack_search'),
    url(r'^searchjson/$', hs_core_views.discovery_json_view.DiscoveryJsonView.as_view(), name='haystack_json_search'),
    url(r'^my-resources/$', hs_core_views.resource_frontend.my_resources, name='my_resources'),
    url(r'^collaborate/$', hs_core_views.CollaborateView.as_view(), name='collaborate'),
    url(r'^my-groups/$', hs_core_views.MyGroupsView.as_view(), name='my_groups'),
    url(r'^group/(?P<group_id>[0-9]+)', hs_core_views.GroupView.as_view(), name='group'),


    url("^inplaceeditform/", include("inplaceeditform.urls")),


    url(r'^user/(?P<user_id>\d*)/', theme.UserProfileView.as_view(), name='profile'),
    url(r'^profile/$', theme.update_user_profile, name='update_profile'),
    url(r'^accounts/signup/', 'theme.views.signup', name='signup'),
    url(r'^deactivate_account/$', theme.deactivate_user, name='deactivate_account'),
    url(r'^delete_irods_account/$', theme.delete_irods_account, name='delete_irods_account'),
    url(r'^create_irods_account/$', theme.create_irods_account, name='create_irods_account'),
    url(r'^accounts/login/$', theme.login, name='login'),
    url(r'^accounts/logout/$', theme.logout, name='logout'),
    url(r'^email_verify/(?P<new_email>.*)/(?P<token>[-\w]+)/(?P<uidb36>[-\w]+)/', theme.email_verify, name='email_verify'),
    url(r'^verify/(?P<token>[0-9a-zA-Z:_\-]*)/', 'hs_core.views.verify'),

    url(r'^django_irods/', include('django_irods.urls')),
    url(r'^autocomplete/', include('autocomplete_light.urls')),

    url(r'^timeseries/sqlite/update/(?P<resource_id>[A-z0-9\-_]+)', hs_ts_views.update_sqlite_file, name='update_sqlite_file'),

    url('^hsapi/', include('hs_rest_api.urls')),
    url('^hsapi/', include('hs_core.urls')),
    url('', include('hs_core.resourcemap_urls')),
    url('', include('hs_core.metadata_terms_urls')),
    url('', include('hs_core.debug_urls')),
    url('^hsapi/', include('ref_ts.urls')),
    url('^irods/', include('irods_browser_app.urls')),
    url('^hs_metrics/', include('hs_metrics.urls')),
    url('^hsapi/', include('hs_model_program.urls')),
    url('^hsapi/', include('hs_labels.urls')),
    url('^hsapi/', include('hs_collection_resource.urls')),
    url('^hsapi/', include('hs_file_types.urls')),
    url('^hsapi/', include('hs_app_netCDF.urls')),

    url(r"^tests/$", TemplateView.as_view(template_name='tests.html'), name="tests"),
    url(r'^robots\.txt$', include('robots.urls')),
    url(r'^tracking/reports/profiles/$', tracking.VisitorProfileReport.as_view(), name='tracking-report-profiles'),
    url(r'^tracking/reports/history/$', tracking.HistoryReport.as_view(), name='tracking-report-history'),
    url(r'^tracking/$', tracking.UseTrackingView.as_view(), name='tracking'),
    url(r'^tracking/applaunch/', tracking.AppLaunch.as_view(), name='tracking-applaunch'),

    url("^", include("mezzanine.urls")),
)

# Filebrowser admin media library.
if getattr(settings, "PACKAGE_NAME_FILEBROWSER") in settings.INSTALLED_APPS:
    urlpatterns += i18n_patterns("",
        ("^admin/media-library/", include("%s.urls" %
                                        settings.PACKAGE_NAME_FILEBROWSER)),
    )

if settings.DEBUG is False:   # if DEBUG is True it will be served automatically
  urlpatterns += patterns('',
  url(r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.STATIC_ROOT}),
)

if 'heartbeat' in settings.INSTALLED_APPS:
  from heartbeat.urls import urlpatterns as heartbeat_urls

  urlpatterns += [
    url(r'^heartbeat/', include(heartbeat_urls))
  ]

# Adds ``STATIC_URL`` to the context of error pages, so that error
# pages can use JS, CSS and images.
handler400 = "hs_core.views.error_handlers.bad_request"
handler403 = "hs_core.views.error_handlers.permission_denied"
handler404 = "hs_core.views.error_handlers.page_not_found"
handler500 = "hs_core.views.error_handlers.server_error"
