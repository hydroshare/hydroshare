# from autocomplete_light import shortcuts as autocomplete_light
from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.generic.base import RedirectView
from mezzanine.conf import settings
from mezzanine.core.views import direct_to_template  # noqa
from mezzanine.pages.views import page

import hs_communities.views.communities
from hs_core import autocomplete_light_registry as alr
from hs_core import views as hs_core_views
from hs_core.views.oauth2_view import GroupAuthorizationView
from hs_discover.views import SearchAPI, SearchView
from hs_rest_api2.urls import hsapi2_urlpatterns
from hs_rest_api.urls import hsapi_urlpatterns
from hs_sitemap.views import sitemap
from hs_tracking import views as tracking
from theme import views as theme
from theme.views import LogoutView, delete_resource_comment, oidc_signup

# autocomplete_light.autodiscover()
admin.autodiscover()

# Add the urlpatterns for any custom Django applications here.
# You can also change the ``home`` view to add your own functionality
# to the project's homepage.
urlpatterns = []
if settings.ENABLE_OIDC_AUTHENTICATION:
    urlpatterns += i18n_patterns(
        path("admin/login/", RedirectView.as_view(url='/oidc/authenticate'), name="admin_login"),
        path("sign-up/", oidc_signup, name='sign-up'),
        path("accounts/logout/", LogoutView.as_view(), name='logout'),
        path("accounts/login/", RedirectView.as_view(url='/oidc/authenticate'), name="login"),
        path('oidc/', include('mozilla_django_oidc.urls')),
    )

urlpatterns += i18n_patterns(
    # Change the admin prefix here to use an alternate URL for the
    # admin interface, which would be marginally more secure.
    path("admin/", include(admin.site.urls)),
    path("o/", include("oauth2_provider.urls", namespace="oauth2_provider")),
    path(
        "o/groupauthorize/<int:group_id>/",
        GroupAuthorizationView.as_view(),
        name="group-authorize",
    ),
    re_path("^r/(?P<shortkey>[A-z0-9\-_]+)", hs_core_views.short_url), # noqa
    path(
        "tracking/reports/profiles/",
        tracking.VisitorProfileReport.as_view(),
        name="tracking-report-profiles",
    ),
    path(
        "tracking/reports/history/",
        tracking.HistoryReport.as_view(),
        name="tracking-report-history",
    ),
    path("tracking/", tracking.UseTrackingView.as_view(), name="tracking"),
    path("tracking/applaunch/", tracking.AppLaunch.as_view(), name="tracking-applaunch"),
    path("user/", theme.UserProfileView.as_view()),
    re_path(r"^user/(?P<user>.*)/", theme.UserProfileView.as_view()),
    path("comment/", theme.comment),
    re_path(
        r"^comment/delete/(?P<id>.*)/$",
        delete_resource_comment,
        name="delete_resource_comment",
    ),
    path("rating/", theme.rating),
    re_path(
        r"^profile/(?P<profile_user_id>.*)/$",
        theme.update_user_profile,
        name="update_profile",
    ),
    re_path(r"^act-on-quota-request/(?P<quota_request_id>[0-9]+)/(?P<action>[a-z]+)/$",
            theme.act_on_quota_request, name='act_on_quota_request_noauth'),
    re_path(
        r'^act-on-quota-request/(?P<quota_request_id>[0-9]+)/(?P<action>[a-z]+)/(?P<uidb36>[-\w]+)/(?P<token>[-\w]+)/$',
        theme.act_on_quota_request, name='act_on_quota_request'),
    path("quota-request/", theme.quota_request, name='quota_request'),
    path("update_password/", theme.update_user_password, name="update_password"),
    re_path(
        r"^resend_verification_email/(?P<email>.*)/",
        theme.resend_verification_email,
        name="resend_verification_email",
    ),
    path(
        "reset_password_request/",
        theme.request_password_reset,
        name="reset_password_request",
    ),
    path(
        "new_password_for_reset/",
        theme.UserPasswordResetView.as_view(),
        name="new_password_for_reset",
    ),
    path(
        "confirm_reset_password/",
        theme.reset_user_password,
        name="confirm_reset_password",
    ),
    path("deactivate_account/", theme.deactivate_user, name="deactivate_account"),
    path("landingPage/", theme.landingPage, name="landing_page"),
    path("home/", theme.dashboard, name="dashboard"),
    path("", theme.home_router, name="home_router"),
    re_path(
        r"^email_verify/(?P<new_email>.*)/(?P<token>[-\w]+)/(?P<uidb36>[-\w]+)/",
        theme.email_verify,
        name="email_verify",
    ),
    re_path(
        r"^email_verify_password_reset/(?P<token>[-\w]+)/(?P<uidb36>[-\w]+)/",
        theme.email_verify_password_reset,
        name="email_verify_password_reset",
    ),
    re_path(r"^verify/(?P<token>[0-9a-zA-Z:_\-]*)/", hs_core_views.verify),
    path("django_irods/", include("django_irods.urls")),
    # path("autocomplete/", include("autocomplete_light.urls")),
    path("discoverapi/", SearchAPI.as_view(), name="DiscoverAPI"),
    path("search/", SearchView.as_view(), name="Discover"),
    path(
        "topics/",
        hs_communities.views.communities.TopicsView.as_view(),
        name="topics",
    ),
    path("sitemap/", sitemap, name="sitemap"),
    path("sitemap", include("hs_sitemap.urls")),
    path("groups", hs_core_views.FindGroupsView.as_view(), name="groups"),
    path(
        "communities/",
        hs_communities.views.communities.FindCommunitiesView.as_view(),
        name="communities",
    ),
    path(
        "community/<int:community_id>/",
        hs_communities.views.communities.CommunityView.as_view(),
        name="community",
    ),
    path(
        "communities/manage-requests/",
        hs_communities.views.communities.CommunityCreationRequests.as_view(),
        name="manage_requests",
    ),
    path(
        "communities/manage-requests/<int:rid>/",
        hs_communities.views.communities.CommunityCreationRequest.as_view(),
        name="manage_request"
    ),
    path(
        "collaborate/",
        hs_communities.views.communities.CollaborateView.as_view(),
        name="collaborate",
    ),
    path("my-resources/", hs_core_views.my_resources, name="my_resources"),
    path(
        "my-resources-counts/",
        hs_core_views.my_resources_filter_counts,
        name="my_resources_counts",
    ),
    path("my-groups/", hs_core_views.MyGroupsView.as_view(), name="my_groups"),
    path(
        "my-communities/",
        hs_communities.views.communities.MyCommunitiesView.as_view(),
        name="my_communities",
    ),
    re_path(
        r"^group/(?P<group_id>[0-9]+)", hs_core_views.GroupView.as_view(), name="group"
    ),
    path("apps/", hs_core_views.apps.AppsView.as_view(), name="apps"),
    path("user-autocomplete/", alr.UserAutocompleteView.as_view(), name="user-autocomplete"),
    path("group-autocomplete/", alr.GroupAutocompleteView.as_view(), name="group-autocomplete"),
)

# Filebrowser admin media library.
if getattr(settings, "PACKAGE_NAME_FILEBROWSER") in settings.INSTALLED_APPS:
    urlpatterns += i18n_patterns(
        path(
            "admin/media-library/",
            include("%s.urls" % settings.PACKAGE_NAME_FILEBROWSER),
        ),
    )

urlpatterns += hsapi_urlpatterns + hsapi2_urlpatterns

# Put API URLs before Mezzanine so that Mezzanine doesn't consume them
urlpatterns += [
    path("", include("hs_core.resourcemap_urls")),
    path("", include("hs_core.metadata_terms_urls")),
    path("", include("hs_core.debug_urls")),
    path("irods/", include("irods_browser_app.urls")),
    path("access/", include("hs_access_control.urls")),
    path("hs_metrics/", include("hs_metrics.urls")),
]

# robots.txt URLs for django-robots
urlpatterns += [
    path(r"robots\.txt", include("robots.urls")),
]
from django.views.static import serve  # noqa

if settings.DEBUG is False and not settings.ENABLE_STATIC_CLOUD_STORAGE:
    # if DEBUG is True it will be served automatically
    urlpatterns += [
        re_path(r"^static/(?P<path>.*)$", serve, {"document_root": settings.STATIC_ROOT}),
    ]

if "heartbeat" in settings.INSTALLED_APPS:
    from heartbeat.urls import urlpatterns as heartbeat_urls

    urlpatterns += [path("heartbeat/", include(heartbeat_urls))]

if "health_check" in settings.INSTALLED_APPS:
    urlpatterns += [path('ht/', include('health_check.urls'))]

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
    path("tests/", direct_to_template, {"template": "tests.html"}, name="tests"),
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
    # Any impact on this with the new home routing mechanism.
    path("", page, {"slug": "/"}, name="home"),
    # HOMEPAGE FOR A BLOG-ONLY SITE
    # -----------------------------
    # This pattern points the homepage to the blog post listing page,
    # and is useful for sites that are primarily blogs. If you use this
    # pattern, you'll also need to set BLOG_SLUG = "" in your
    # ``settings.py`` module, and delete the blog page object from the
    # page tree in the admin if it was installed.
    # url("^$", "mezzanine.blog.views.blog_post_list", name="home"),
    # Override Mezzanine URLs here, before the Mezzanine URL include
    re_path("^accounts/signup/", theme.signup),
    re_path("^accounts/verify/(?P<uidb36>[-\w]+)/(?P<token>[-\w]+)", theme.signup_verify), # noqa
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
    path("", include("mezzanine.urls")),
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
