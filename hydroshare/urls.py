from __future__ import unicode_literals

from django.conf.urls import include, url
from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin

from mezzanine.core.views import direct_to_template
from mezzanine.conf import settings
from mezzanine.pages.views import page

from autocomplete_light import shortcuts as autocomplete_light

from hs_core.views.discovery_view import DiscoveryView
from hs_core.views.discovery_json_view import DiscoveryJsonView
from hs_sitemap.views import sitemap
from theme import views as theme
from hs_tracking import views as tracking
from hs_core import views as hs_core_views
from hs_app_timeseries import views as hs_ts_views
from hs_app_netCDF import views as nc_views


autocomplete_light.autodiscover()
admin.autodiscover()

# Add the urlpatterns for any custom Django applications here.
# You can also change the ``home`` view to add your own functionality
# to the project's homepage.

urlpatterns = i18n_patterns(
    # Change the admin prefix here to use an alternate URL for the
    # admin interface, which would be marginally more secure.
    url("^admin/", include(admin.site.urls)),
    url(r'^o/', include('oauth2_provider.urls', namespace='oauth2_provider')),
    url("^inplaceeditform/", include("inplaceeditform.urls")),
    url('^r/(?P<shortkey>[A-z0-9\-_]+)', hs_core_views.short_url),
    url(r'^tracking/reports/profiles/$', tracking.VisitorProfileReport.as_view(),
        name='tracking-report-profiles'),
    url(r'^tracking/reports/history/$', tracking.HistoryReport.as_view(),
        name='tracking-report-history'),
    url(r'^tracking/$', tracking.UseTrackingView.as_view(), name='tracking'),
    url(r'^tracking/applaunch/', tracking.AppLaunch.as_view(), name='tracking-applaunch'),
    url(r'^user/$', theme.UserProfileView.as_view()),
    url(r'^user/(?P<user>.*)/', theme.UserProfileView.as_view()),
    url(r'^comment/$', theme.comment),
    url(r'^rating/$', theme.rating),
    url(r'^profile/$', theme.update_user_profile, name='update_profile'),
    url(r'^update_password/$', theme.update_user_password, name='update_password'),
    url(r'^resend_verification_email/(?P<email>.*)/', theme.resend_verification_email,
        name='resend_verification_email'),
    url(r'^reset_password_request/$', theme.request_password_reset,
        name='reset_password_request'),
    url(r'^new_password_for_reset/(?P<token>[-\w]+)/', theme.UserPasswordResetView.as_view(),
        name='new_password_for_reset'),
    url(r'^confirm_reset_password/$', theme.reset_user_password,
        name='confirm_reset_password'),
    url(r'^deactivate_account/$', theme.deactivate_user, name='deactivate_account'),
    url(r'^delete_irods_account/$', theme.delete_irods_account, name='delete_irods_account'),
    url(r'^create_irods_account/$', theme.create_irods_account, name='create_irods_account'),
    url(r'^accounts/login/$', theme.login, name='login'),
    url(r'^email_verify/(?P<new_email>.*)/(?P<token>[-\w]+)/(?P<uidb36>[-\w]+)/',
        theme.email_verify, name='email_verify'),
    url(r'^email_verify_password_reset/(?P<token>[-\w]+)/(?P<uidb36>[-\w]+)/',
        theme.email_verify_password_reset, name='email_verify_password_reset'),
    url(r'^verify/(?P<token>[0-9a-zA-Z:_\-]*)/', hs_core_views.verify),
    url(r'^django_irods/', include('django_irods.urls')),
    url(r'^autocomplete/', include('autocomplete_light.urls')),
    url(r'^search/$', DiscoveryView.as_view(), name='haystack_search'),
    url(r'^searchjson/$', DiscoveryJsonView.as_view(), name='haystack_json_search'),
    url(r'^sitemap/$', sitemap, name='sitemap'),
    url(r'^sitemap', include('hs_sitemap.urls')),
    url(r'^collaborate/$', hs_core_views.CollaborateView.as_view(), name='collaborate'),
    url(r'^my-groups/$', hs_core_views.MyGroupsView.as_view(), name='my_groups'),
    url(r'^group/(?P<group_id>[0-9]+)', hs_core_views.GroupView.as_view(), name='group'),
    url(r'^timeseries/sqlite/update/(?P<resource_id>[A-z0-9\-_]+)', hs_ts_views.update_sqlite_file,
        name='update_sqlite_file'),
    url(r'^apps/$', hs_core_views.apps.AppsView.as_view(), name="apps")
)

# Filebrowser admin media library.
if getattr(settings, "PACKAGE_NAME_FILEBROWSER") in settings.INSTALLED_APPS:
    urlpatterns += i18n_patterns(
        url("^admin/media-library/", include("%s.urls" %
                                        settings.PACKAGE_NAME_FILEBROWSER)),
    )

# Put API URLs before Mezzanine so that Mezzanine doesn't consume them
urlpatterns += [
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
]

# robots.txt URLs for django-robots
urlpatterns += [
    url(r'^robots\.txt', include('robots.urls')),
]
from django.views.static import serve
if settings.DEBUG is False:   # if DEBUG is True it will be served automatically
  urlpatterns += [
  url(r'^static/(?P<path>.*)$', serve, {'document_root': settings.STATIC_ROOT}),
]

if 'heartbeat' in settings.INSTALLED_APPS:
  from heartbeat.urls import urlpatterns as heartbeat_urls

  urlpatterns += [
    url(r'^heartbeat/', include(heartbeat_urls))
  ]

urlpatterns += [
    # We don't want to presume how your homepage works, so here are a
    # few patterns you can use to set it up.

    # HOMEPAGE AS STATIC TEMPLATE
    # ---------------------------
    # This pattern simply loads the index.html template. It isn't
    # commented out like the others, so it's the default. You only need
    # one homepage pattern, so if you use a different one, comment this
    # one out.

    # url("^$", direct_to_template, {"template": "index.html"}, name="home"),
    url(r"^tests/$", direct_to_template, {"template": "tests.html"}, name="tests"),

    # HOMEPAGE AS AN EDITABLE PAGE IN THE PAGE TREE
    # ---------------------------------------------
    # This pattern gives us a normal ``Page`` object, so that your
    # homepage can be managed via the page tree in the admin. If you
    # use this pattern, you'll need to create a page in the page tree,
    # and specify its URL (in the Meta Data section) as "/", which
    # is the value used below in the ``{"slug": "/"}`` part.
    # Also note that the normal rule of adding a custom
    # template per page with the template name using the page's slug
    # doesn't apply here, since we can't have a template called
    # "/.html" - so for this case, the template "pages/index.html"
    # should be used if you want to customize the homepage's template.

    url("^$", page, {"slug": "/"}, name="home"),

    # HOMEPAGE FOR A BLOG-ONLY SITE
    # -----------------------------
    # This pattern points the homepage to the blog post listing page,
    # and is useful for sites that are primarily blogs. If you use this
    # pattern, you'll also need to set BLOG_SLUG = "" in your
    # ``settings.py`` module, and delete the blog page object from the
    # page tree in the admin if it was installed.

    # url("^$", "mezzanine.blog.views.blog_post_list", name="home"),

    # Override Mezzanine URLs here, before the Mezzanine URL include
    url("^accounts/signup/", theme.signup),
    url("^accounts/verify/(?P<uidb36>[-\w]+)/(?P<token>[-\w]+)", theme.signup_verify),

    # MEZZANINE'S URLS
    # ----------------
    # ADD YOUR OWN URLPATTERNS *ABOVE* THE LINE BELOW.
    # ``mezzanine.urls`` INCLUDES A *CATCH ALL* PATTERN
    # FOR PAGES, SO URLPATTERNS ADDED BELOW ``mezzanine.urls``
    # WILL NEVER BE MATCHED!

    # If you'd like more granular control over the patterns in
    # ``mezzanine.urls``, go right ahead and take the parts you want
    # from it, and use them directly below instead of using
    # ``mezzanine.urls``.
    url("^", include("mezzanine.urls")),

    # MOUNTING MEZZANINE UNDER A PREFIX
    # ---------------------------------
    # You can also mount all of Mezzanine's urlpatterns under a
    # URL prefix if desired. When doing this, you need to define the
    # ``SITE_PREFIX`` setting, which will contain the prefix. Eg:
    # SITE_PREFIX = "my/site/prefix"
    # For convenience, and to avoid repeating the prefix, use the
    # commented out pattern below (commenting out the one above of course)
    # which will make use of the ``SITE_PREFIX`` setting. Make sure to
    # add the import ``from django.conf import settings`` to the top
    # of this file as well.
    # Note that for any of the various homepage patterns above, you'll
    # need to use the ``SITE_PREFIX`` setting as well.

    # ("^%s/" % settings.SITE_PREFIX, include("mezzanine.urls"))

]

# Adds ``STATIC_URL`` to the context of error pages, so that error
# pages can use JS, CSS and images.
handler404 = "mezzanine.core.views.page_not_found"
handler500 = "mezzanine.core.views.server_error"
