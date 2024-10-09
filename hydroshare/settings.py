# TEST_RUNNER='django_nose.NoseTestSuiteRunner'
import os
import sys

from PIL import ImageFile

TEST_RUNNER = "hs_core.tests.runner.CustomTestSuiteRunner"
TEST_WITHOUT_MIGRATIONS_COMMAND = "django_nose.management.commands.test.Command"


# import importlib

local_settings_module = os.environ.get("LOCAL_SETTINGS", "hydroshare.local_settings")

######################
# MEZZANINE SETTINGS #
######################

# The following settings are already defined with default values in
# the ``defaults.py`` module within each of Mezzanine's apps, but are
# common enough to be put here, commented out, for convenient
# overriding. Please consult the settings documentation for a full list
# of settings Mezzanine implements:
# http://mezzanine.jupo.org/docs/configuration.html#default-settings

# Controls the ordering and grouping of the admin menu.
#
# ADMIN_MENU_ORDER = (
#     ("Content", ("pages.Page", "blog.BlogPost",
#        "generic.ThreadedComment", ("Media Library", "fb_browse"),)),
#     ("Site", ("sites.Site", "redirects.Redirect", "conf.Setting")),
#     ("Users", ("auth.User", "auth.Group",)),
# )

# A three item sequence, each containing a sequence of template tags
# used to render the admin dashboard.
#
# DASHBOARD_TAGS = (
#     ("blog_tags.quick_blog", "mezzanine_tags.app_list"),
#     ("comment_tags.recent_comments",),
#     ("mezzanine_tags.recent_actions",),
# )

# A sequence of templates used by the ``page_menu`` template tag. Each
# item in the sequence is a three item sequence, containing a unique ID
# for the template, a label for the template, and the template path.
# These templates are then available for selection when editing which
# menus a page should appear in. Note that if a menu template is used
# that doesn't appear in this setting, all pages will appear in it.

# PAGE_MENU_TEMPLATES = (
#     (1, "Top navigation bar", "pages/menus/dropdown.html"),
#     (2, "Left-hand tree", "pages/menus/tree.html"),
#     (3, "Footer", "pages/menus/footer.html"),
# )

# A sequence of fields that will be injected into Mezzanine's (or any
# library's) models. Each item in the sequence is a four item sequence.
# The first two items are the dotted path to the model and its field
# name to be added, and the dotted path to the field class to use for
# the field. The third and fourth items are a sequence of positional
# args and a dictionary of keyword args, to use when creating the
# field instance. When specifying the field class, the path
# ``django.models.db.`` can be omitted for regular Django model fields.
#
# EXTRA_MODEL_FIELDS = (
#     (
#         # Dotted path to field.
#         "mezzanine.blog.models.BlogPost.image",
#         # Dotted path to field class.
#         "somelib.fields.ImageField",
#         # Positional args for field class.
#         ("Image",),
#         # Keyword args for field class.
#         {"blank": True, "upload_to": "blog"},
#     ),
#     # Example of adding a field to *all* of Mezzanine's content types:
#     (
#         "mezzanine.pages.models.Page.another_field",
#         "IntegerField", # 'django.db.models.' is implied if path is omitted.
#         ("Another name",),
#         {"blank": True, "default": 1},
#     ),
# )

# Setting to turn on featured images for blog posts. Defaults to False.
#
# BLOG_USE_FEATURED_IMAGE = True

# If True, the south application will be automatically added to the
# INSTALLED_APPS setting.
USE_SOUTH = False


########################
# MAIN DJANGO SETTINGS #
########################

# People who get code error notifications.
# In the format (('Full Name', 'email@example.com'),
#                ('Full Name', 'anotheremail@example.com'))
ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)
MANAGERS = ADMINS

# Hosts/domain names that are valid for this site; required if DEBUG is False
# https://docs.djangoproject.com/en/3.2/ref/settings/#allowed-hosts
ALLOWED_HOSTS = ["*"]

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = None

# If you set this to True, Django will use timezone-aware datetimes.
USE_TZ = True

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = "en"

# Supported languages
def _(s): return s # noqa


LANGUAGES = (("en", _("English")),)

# A boolean that turns on/off debug mode. When set to ``True``, stack traces
# are displayed for error pages. Should always be set to ``False`` in
# production. Best set to ``True`` in local_settings.py
DEBUG = False

# A boolean that determines whether tasks related emails should be sent.
# Best set to ``True`` in local_settings.py
DISABLE_TASK_EMAILS = False

DEFAULT_FROM_EMAIL = 'hydro@hydroshare.org'
DEFAULT_SUPPORT_EMAIL = 'support@hydroshare.org'
DEFAULT_DEVELOPER_EMAIL = 'developer@hydroshare.org'

# Integer seconds that worker should allocate every night to repair_resource file discrepancies
NIGHTLY_RESOURCE_REPAIR_DURATION = 60 * 60

# Integer seconds that worker should allocate every night to generating filesystem metadata
NIGHTLY_GENERATE_FILESYSTEM_METADATA_DURATION = 60 * 60 * 4  # 4 hours

# Should resource owners be notified of automated resource repair?
NOTIFY_OWNERS_AFTER_RESOURCE_REPAIR = False

# Whether a user's session cookie expires when the Web browser is closed.
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = False

# Tuple of IP addresses, as strings, that:
#   * See debug comments, when DEBUG is true
#   * Receive x-headers
INTERNAL_IPS = ("127.0.0.1",)

# make django file uploader to always write uploaded file to a temporary directory
# rather than holding uploaded file in memory for small files. This is due to
# the difficulty of metadata extraction from an uploaded file being held in memory
# by Django, e.g., gdal raster metadata extraction opens file from disk to extract
# metadata. Besides, performance gain from holding small uploaded files in memory
# is not that great for our project use case
FILE_UPLOAD_MAX_MEMORY_SIZE = 0

# the size that a file will be chunked for resumable download
RANGED_FILE_READER_BLOCK_SIZE = 1024 * 1024  # 1MB

# the size of the buffer that will be used when dumping unneeded bytes from head of a resumed file
RANGED_FILE_READER_DUMP_SIZE = 1024 * 1024 * 1024  # 1GB

# TODO remove MezzanineBackend after conflicting users have been removed
AUTHENTICATION_BACKENDS = [
    "theme.backends.CaseInsensitiveMezzanineBackend",
]

# Wether to enable OIDC auth via mozilla_django_oidc
# Default false to enable local development
# Set to true in local_settings if desired for specific deployment
ENABLE_OIDC_AUTHENTICATION = False

# If OIDC is enabled, the following additional settings should be defined in local_settings
# OIDC_OP_AUTHORIZATION_ENDPOINT = "https://auth.cuahsi.io/realms/CUAHSI/protocol/openid-connect/auth"
# OIDC_OP_TOKEN_ENDPOINT = "https://auth.cuahsi.io/realms/CUAHSI/protocol/openid-connect/token"
# OIDC_OP_USER_ENDPOINT = "https://auth.cuahsi.io/realms/CUAHSI/protocol/openid-connect/userinfo"
# OIDC_RP_SIGN_ALGO = "RS256"
# OIDC_OP_JWKS_ENDPOINT = "https://auth.cuahsi.io/realms/CUAHSI/protocol/openid-connect/certs"
OIDC_RP_CLIENT_ID = 'hydroshare'
OIDC_RP_CLIENT_SECRET = 'blah'
KEYCLOAK_ADMIN_USERNAME = 'blah'
KEYCLOAK_ADMIN_PASSWORD = 'blah'
# LOGIN_REDIRECT_URL = '/home/'
# LOGIN_URL = '/oidc/authenticate/'
# OIDC_CHANGE_PASSWORD_URL = "https://auth.cuahsi.io/realms/CUAHSI/account?#/security/signingin"
# ALLOW_LOGOUT_GET_METHOD = True
# LOGOUT_REDIRECT_URL = '/'
# OIDC_OP_LOGOUT_ENDPOINT = "https://auth.cuahsi.io/realms/CUAHSI/protocol/openid-connect/logout"

# The following two settings will logout of OIDC during signout
# If these two settings are not enabled,
# the user will be redirected to auth.cuahsi.io to choose if they want to logout of SSO
# OIDC_OP_LOGOUT_URL_METHOD = 'hs_core.authentication.provider_logout'
# OIDC_STORE_ID_TOKEN = True

# Whether or not the OIDC provider should verify SSL certificates from the identity provider
# OIDC_VERIFY_SSL = True

OIDC_KEYCLOAK_URL = "https://auth.cuahsi.org/"
OIDC_KEYCLOAK_REALM = "CUAHSI"

# Enables publishing discoverable resources to Google PubSub (hs_core/pubsub_discovery_processor.py)
# Requires a service account json file with PubSub permissions to be placed at the root of the
# project with the name service-account-pubsub.json
PUBLISH_DISCOVERABLE = False

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
    # "django.contrib.staticfiles.finders.DefaultStorageFinder",
    # We disable the DefaultStorageFinder because otherwise it will search for static files in Google Cloud Storage
    # https://docs.djangoproject.com/en/3.2/ref/settings/#staticfiles-finders
)

# The numeric mode to set newly-uploaded files to. The value should be
# a mode you'd pass directly to os.chmod.
FILE_UPLOAD_PERMISSIONS = 0o644

# Alternative tmp folder
FILE_UPLOAD_TEMP_DIR = "/tmp"

FILE_UPLOAD_MAX_SIZE = 25 * 1024  # 25GB in MB

# https://docs.djangoproject.com/en/3.2/ref/settings/#data-upload-max-memory-size
DATA_UPLOAD_MAX_MEMORY_SIZE = 100 * 1024 * 1024  # 100 MB in Bytes

#############
# DATABASES #
#############

DATABASES = {
    "default": {
        # Add "postgresql_psycopg2", "mysql", "sqlite3" or "oracle".
        "ENGINE": "django.db.backends.",
        # DB name or path to database file if using sqlite3.
        "NAME": "",
        # Not used with sqlite3.
        "USER": "",
        # Not used with sqlite3.
        "PASSWORD": "",
        # Set to empty string for localhost. Not used with sqlite3.
        "HOST": "",
        # Set to empty string for default. Not used with sqlite3.
        "PORT": "",
    }
}

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

#########
# PATHS #
#########


# Full filesystem path to the project.
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(PROJECT_ROOT)

# Name of the directory for the project.
PROJECT_DIRNAME = PROJECT_ROOT.split(os.sep)[-1]

# Every cache key will get prefixed with this value - here we set it to
# the name of the directory the project is in to try and use something
# project specific.
CACHE_MIDDLEWARE_KEY_PREFIX = PROJECT_DIRNAME

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"

#  Had to change STATIC_URL as required since django 2.2 when running in DEBUG mode
#  Django does the following check in django =>2.2:
# if (settings.DEBUG and settings.MEDIA_URL and settings.STATIC_URL and
# 		settings.MEDIA_URL.startswith(settings.STATIC_URL)):
# 	raise ImproperlyConfigured(
# 		"runserver can't serve media if MEDIA_URL is within STATIC_URL."
# 	)
# that means path for STATIC_URL can't be a parent directory of path for MEDIA_URL
# Ref: https://docs.djangoproject.com/en/2.2/ref/settings/#media-root
STATIC_URL = "/static/static/"

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = os.path.join(PROJECT_ROOT, STATIC_URL.strip("/"))

# using this storage class might cause issues for future tests
# The documentation suggests using the default storage backend when testing
# https://docs.djangoproject.com/en/1.11/ref/contrib/staticfiles/#django.contrib.staticfiles.storage.ManifestStaticFilesStorage.manifest_strict
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "hydroshare.storage.ForgivingManifestStaticFilesStorage",
    },
}

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"

# Note: MEDIA_URL needs to be set to a path so that STATIC_URL is not a parent folder of MEDIA_URL
MEDIA_URL = "/static/media/"

# Sorl settings for generating thumbnails
THUMBNAIL_PRESERVE_FORMAT = True
THUMBNAIL_QUALITY = 95

# Allow PIL to ignore imgs with lots of metadata

ImageFile.LOAD_TRUNCATED_IMAGES = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
MEDIA_ROOT = os.path.join(PROJECT_ROOT, *MEDIA_URL.strip("/").split("/"))

# ----- START of settings for using Google Cloud Storage for static files ----- |
ENABLE_STATIC_CLOUD_STORAGE = False
# Whether to use Google Cloud Storage for static files
# Settings documented here: https://django-storages.readthedocs.io/en/latest/backends/gcloud.html#settings
# By default, this is set to False, and static files are served from the local filesystem
# To enable Google Cloud Storage, the following settings should be added to local_settings.py
# Additionally, a google service account json file should be placed at the root of the project
# Service account should have permissions to write to the bucket
# lastly, when you build the discover VUE app, you should set export the VUE_APP_BUCKET_URL_PUBLIC_PATH env var
# this value should be the same as the STATIC_URL that you set in django local_settings.py

# ENABLE_STATIC_CLOUD_STORAGE = True
# from google.oauth2 import service_account
# from datetime import timedelta
# PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
# BASE_DIR = os.path.dirname(PROJECT_ROOT)
# GS_PROJECT_ID = 'hydroshare-gc-project'
# GS_BUCKET_NAME = 'hydroshare-static-media-bucket'
# GS_BLOB_CHUNK_SIZE = 1024 * 256 * 40  # Needed for uploading large streams
# GS_EXPIRATION = timedelta(minutes=5)
# GS_SERVICE_ACCOUNT_FILENAME = 'hydroshare-gcs-sa.json'
# # necessary to prevent RuntimeError: Max post-process passes exceeded.
# GS_QUERYSTRING_AUTH = False
# GS_DEFAULT_ACL = None
# GS_CREDENTIALS = service_account.Credentials.from_service_account_file(
#     os.path.join(BASE_DIR, GS_SERVICE_ACCOUNT_FILENAME)
# )
# STATICFILES_STORAGE = 'hydroshare.storage.Static'
# THUMBNAIL_STORAGE = 'storages.backends.gcloud.GoogleCloudStorage'
# DEFAULT_FILE_STORAGE = 'hydroshare.storage.MediaeGoogleCloudStorage'
# # the media is served from the root of the bucket
# MEDIA_URL = f'https://storage.googleapis.com/{GS_BUCKET_NAME}/'
# # the static files are served from a static/ dir in the bucket
# STATIC_URL = f'https://storage.googleapis.com/{GS_BUCKET_NAME}/static/'
# MEDIA_ROOT = MEDIA_URL
# STATIC_ROOT = STATIC_URL
# ----- END of settings for using Google Cloud Storage for static files ----- |

# Package/module name to import the root urlpatterns from for the project.
ROOT_URLCONF = "%s.urls" % PROJECT_DIRNAME

ADAPTOR_INPLACEEDIT_EDIT = "hs_core.models.HSAdaptorEditInline"
INPLACE_SAVE_URL = "/hsapi/save_inline/"

################
# APPLICATIONS #
################

INSTALLED_APPS = (
    "test_without_migrations",
    "dal",
    "dal_select2",
    "django.contrib.admin",
    "django.contrib.auth",
    "oauth2_provider",
    "corsheaders",
    "django.contrib.contenttypes",
    "django.contrib.redirects",
    "django.contrib.sessions",
    "django.contrib.sites",
    "django.contrib.sitemaps",
    "django.contrib.staticfiles",
    "django.contrib.gis",
    "django.contrib.postgres",
    "django.contrib.messages",
    "django_nose",
    "django_irods",
    "drf_yasg",
    "theme",
    "theme.blog_mods",
    "heartbeat",
    "mezzanine.boot",
    "mezzanine.conf",
    "mezzanine.core",
    "mezzanine.generic",
    "mezzanine.blog",
    "mezzanine.forms",
    "mezzanine.pages",
    "mezzanine.galleries",
    "crispy_forms",
    "crispy_bootstrap3",
    "mezzanine.accounts",
    "haystack",
    "rest_framework",
    "robots",
    "sorl.thumbnail",
    "hs_core",
    "hs_access_control",
    "hs_labels",
    "hs_metrics",
    "irods_browser_app",
    "widget_tweaks",
    "hs_tools_resource",
    "hs_sitemap",
    "hs_collection_resource",
    "hs_tracking",
    "hs_file_types",
    "hs_composite_resource",
    "hs_rest_api",
    "hs_rest_api2",
    "hs_dictionary",
    "hs_odm2",
    "security",
    "markdown",
    "hs_communities",
    "hs_discover",
    "health_check",
    "health_check.db",
    "health_check.cache",
    "health_check.storage",
    "health_check.contrib.migrations",
    "health_check.contrib.celery",
    "health_check.contrib.celery_ping",
    "health_check.contrib.psutil",
    "health_check.contrib.rabbitmq",
    "mozilla_django_oidc",
    'django_tus',
)

TUS_UPLOAD_DIR = '/tmp/tus_upload'
TUS_DESTINATION_DIR = '/tmp/tus_completed'
TUS_FILE_NAME_FORMAT = 'increment'  # Other options are: 'random-suffix', 'random', 'keep'
TUS_EXISTING_FILE = 'error'  # Other options are: 'overwrite',  'error', 'rename'

SWAGGER_SETTINGS = {
    "DEFAULT_GENERATOR_CLASS": "hs_rest_api2.serializers.NestedSchemaGenerator"
}

OAUTH2_PROVIDER_APPLICATION_MODEL = "oauth2_provider.Application"

# These apps are excluded by hs_core.tests.runner.CustomTestSuiteRunner
# All apps beginning with "django." or "mezzanine." are also excluded by default
APPS_TO_NOT_RUN = (
    "rest_framework",
    "django_nose",
    "grappelli_safe",
    "django_irods",
    "crispy_forms",
    "autocomplete_light",
    "widget_tweaks",
    "oauth2_provider",
    "debug_toolbar",
    "corsheaders",
    "security",
    "django_comments",
    "haystack" "test_without_migrations",
    "robots",
    "heartbeat",
    "filebrowser_safe"
    # etc...
)

# List of processors used by RequestContext to populate the context.
# Each one should be a callable that takes the request object as its
# only parameter and returns a dictionary to add to the context.
# TEMPLATE_CONTEXT_PROCESSORS = ()

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "hs_core", "templates")],
        "OPTIONS": {
            "context_processors": [
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.debug",
                "django.template.context_processors.i18n",
                "django.template.context_processors.static",
                "django.template.context_processors.media",
                "django.template.context_processors.request",
                "django.template.context_processors.tz",
                "mezzanine.conf.context_processors.settings",
                "mezzanine.pages.context_processors.page",
            ],
            "loaders": [
                "mezzanine.template.loaders.host_themes.Loader",
                "django.template.loaders.filesystem.Loader",
                "django.template.loaders.app_directories.Loader",
            ],
            "builtins": [
                "django.templatetags.static",
            ],
            "libraries": {
                "staticfiles": "django.templatetags.static",
            },
        },
    },
]

# List of middleware classes to use. Order is important; in the request phase,
# these middleware classes will be applied in the order given, and in the
# response phase the middleware will be applied in reverse order.
MIDDLEWARE = (
    "mezzanine.core.middleware.UpdateCacheMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "hs_tools_resource.middleware.CheckRequest",  # before CsrfViewMiddleware
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "mezzanine.core.request.CurrentRequestMiddleware",
    "mezzanine.core.middleware.RedirectFallbackMiddleware",
    "mezzanine.core.middleware.AdminLoginInterfaceSelectorMiddleware",
    "mezzanine.core.middleware.SitePermissionMiddleware",
    # Uncomment the following if using any of the SSL settings:
    # "mezzanine.core.middleware.SSLRedirectMiddleware",
    "mezzanine.pages.middleware.PageMiddleware",
    "mezzanine.core.middleware.FetchFromCacheMiddleware",
    "hs_core.robots.RobotFilter",
    "hs_tracking.middleware.Tracking",
)

# security settings
USE_SECURITY = False
if USE_SECURITY:
    MIDDLEWARE += (
        "security.middleware.XssProtectMiddleware",
        "security.middleware.ContentSecurityPolicyMiddleware",
        "security.middleware.ContentNoSniff",
        "security.middleware.XFrameOptionsMiddleware",
        "django.middleware.security.SecurityMiddleware",
    )

# Store these package names here as they may change in the future since
# at the moment we are using custom forks of them.
PACKAGE_NAME_FILEBROWSER = "filebrowser_safe"
PACKAGE_NAME_GRAPPELLI = "grappelli_safe"

#########################
#  CORS/OAUTH SETTINGS  #
#########################

# TODO: change this to the actual origins we wish to support
CORS_ORIGIN_ALLOW_ALL = True

#########################
# OPTIONAL APPLICATIONS #
#########################

# These will be added to ``INSTALLED_APPS``, only if available.
OPTIONAL_APPS = (
    # "debug_toolbar",
    # debug_toolbar disabled for GCS storage
    # debug_toolbar calls ".path" on a storage object, which is not supported by GCS storage
    "django_extensions",
    # "compressor",
    PACKAGE_NAME_FILEBROWSER,
    PACKAGE_NAME_GRAPPELLI,
)

DEBUG_TOOLBAR_CONFIG = {"INTERCEPT_REDIRECTS": False}

###################
# DEPLOY SETTINGS #
###################

# These settings are used by the default fabfile.py provided.
# Check fabfile.py for defaults.

# FABRIC = {
#     "SSH_USER": "", # SSH username
#     "SSH_PASS":  "", # SSH password (consider key-based authentication)
#     "SSH_KEY_PATH":  "", # Local path to SSH key file, for key-based auth
#     "HOSTS": [], # List of hosts to deploy to
#     "VIRTUALENV_HOME":  "", # Absolute remote path for virtualenvs
#     "PROJECT_NAME": "", # Unique identifier for project
#     "REQUIREMENTS_PATH": "", # Path to pip requirements, relative to project
#     "GUNICORN_PORT": 8000, # Port gunicorn will listen on
#     "LOCALE": "en_US.UTF-8", # Should end with ".UTF-8"
#     "LIVE_HOSTNAME": "www.example.com", # Host for public site.
#     "REPO_URL": "", # Git or Mercurial remote repo URL for the project
#     "DB_PASS": "", # Live database password
#     "ADMIN_PASS": "", # Live admin user password
#     "SECRET_KEY": SECRET_KEY,
#     "NEVERCACHE_KEY": NEVERCACHE_KEY,
# }


ACCOUNTS_PROFILE_MODEL = "theme.UserProfile"
CRISPY_TEMPLATE_PACK = "bootstrap3"

DEFAULT_AUTHENTICATION_CLASSES = (
    "rest_framework.authentication.BasicAuthentication",
    "rest_framework.authentication.SessionAuthentication",
    "oauth2_provider.contrib.rest_framework.OAuth2Authentication",
)

REST_FRAMEWORK = {
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 100,
    "PAGE_SIZE_QUERY_PARAM": "PAGE_SIZE",
    "EXCEPTION_HANDLER": "rest_framework.views.exception_handler",
    "DEFAULT_AUTHENTICATION_CLASSES": DEFAULT_AUTHENTICATION_CLASSES,
    "DEFAULT_VERSIONING_CLASS": "rest_framework.versioning.NamespaceVersioning",
}

SOLR_HOST = os.environ.get("SOLR_PORT_8983_TCP_ADDR", "localhost")
SOLR_PORT = "8983"
HAYSTACK_CONNECTIONS = {
    "default": {
        "ENGINE": "haystack.backends.solr_backend.SolrEngine",
        "URL": "http://{SOLR_HOST}:{SOLR_PORT}/solr/collection1".format(**globals()),
        "ADMIN_URL": "http://{SOLR_HOST}:{SOLR_PORT}/solr/admin/cores".format(
            **globals()
        ),
        # ...or for multicore...
        # 'URL': 'http://127.0.0.1:8983/solr/mysite',
    },
}
HAYSTACK_SIGNAL_PROCESSOR = (
    "hs_core.hydro_realtime_signal_processor.HydroRealtimeSignalProcessor"
)


# customized value for password reset token, email verification and group invitation link token
# to expire in 7 days
PASSWORD_RESET_TIMEOUT = 60 * 60 * 24 * 7

# customized temporary file path for large files retrieved from iRODS user zone for metadata
# extraction
TEMP_FILE_DIR = "/tmp"

####################
# OAUTH TOKEN SETTINGS #
####################

OAUTH2_PROVIDER = {
    "ACCESS_TOKEN_EXPIRE_SECONDS": 2592000,  # 30 days
    "PKCE_REQUIRED": False,
}

####################
# LOGGING SETTINGS #
####################

# Using Google Cloud Logging will format logs in a structured way that can be parsed by Google Cloud Logging
USE_CLOUD_LOGGING = False

if USE_CLOUD_LOGGING:
    import google.cloud.logging as gcloud_logging
    from google.cloud.logging_v2.handlers import setup_logging

    client = gcloud_logging.Client()
    handler = gcloud_logging.handlers.StructuredLogHandler()
    setup_logging(handler)
else:
    LOGGING = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "verbose": {
                "format": "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s",
                "datefmt": "%d/%b/%Y %H:%M:%S",
            },
            "simple": {
                "format": "[%(asctime)s] %(levelname)s %(message)s",
                "datefmt": "%d/%b/%Y %H:%M:%S",
            },
        },
        "handlers": {
            "djangolog": {
                "level": "DEBUG",
                "class": "logging.handlers.RotatingFileHandler",
                "filename": "/hydroshare/log/django.log",
                "formatter": "verbose",
                "maxBytes": 1024 * 1024 * 15,  # 15MB
                "backupCount": 10,
            },
            "hydrosharelog": {
                "level": "DEBUG",
                "class": "logging.handlers.RotatingFileHandler",
                "filename": "/hydroshare/log/hydroshare.log",
                "formatter": "verbose",
                "maxBytes": 1024 * 1024 * 15,  # 15MB
                "backupCount": 10,
            },
            "celerylog": {
                "level": "DEBUG",
                "class": "logging.handlers.RotatingFileHandler",
                "filename": "/hydroshare/log/celery.log",
                "formatter": "verbose",
                "maxBytes": 1024 * 1024 * 15,  # 15MB
                "backupCount": 10,
            },
        },
        "loggers": {
            "django": {
                "handlers": ["djangolog"],
                "propagate": False,
                "level": "DEBUG",
            },
            # https://docs.djangoproject.com/en/1.11/topics/logging/#django-template
            "django.template": {
                "handlers": ["djangolog"],
                "level": "INFO",
                "propagate": False,
            },
            "django.db.backends": {
                "handlers": ["djangolog"],
                "level": "WARNING",
                "propagate": False,
            },
            "celery": {
                "handlers": ["celerylog"],
                "level": "WARNING",
                "propagate": False,
            },
            # Catch-all logger for HydroShare apps
            "": {"handlers": ["hydrosharelog"], "propagate": False, "level": "DEBUG"},
        },
    }

# hs_tracking settings
TRACKING_SESSION_TIMEOUT = 60 * 15
TRACKING_PROFILE_FIELDS = [
    "title",
    "user_type",
    "subject_areas",
    "public",
    "state",
    "country",
]
TRACKING_USER_FIELDS = ["username", "email", "first_name", "last_name"]


# Content Security Policy
# See http://django-csp.readthedocs.io/en/latest/configuration.html#configuration-chapter
# sha256-* strings are hashes of inline scripts and styles

CSP_DICT = {
    "default-src": [
        "none",
    ],
    "script-src": [
        "self",
        "*.google.com",
        "*.googleapis.com",
        "*.rawgit.com",
        "*.cloudflare.com",
        "*.datatables.net ",
        "*.github.io",
        "'sha256-knR/FBinurfPQntk2aEOJBVdKTB+jAzLBk5er9r0rEI='",
        "'sha256-s9/ymLoZ5XUQCLrYU4LA0197Ys8F+MChBBmMgWyBUm4='",
        "'sha256-r8WSQMRpNued376HSguoGRJRnDD1TXEdhbfJ9agQytA='",
        "'sha256-EeeHsgrKQ0j+QXY9+NqkhS9pB8fZ4iPEiytjK3sVD/k='",
        "'sha256-JB94IjPO9ws/1kVTgg5lq3sUp/3Yt/1gm4wx82JRCVE='",
        "'sha256-5ps1OUcNv+F/rpDQlMFLOuF67quHYXVbFf9yOJNjqaw='",
        "'sha256-ptl8NJjRX6En62nAGX95mPmBq5Zq1p7JIsTIzhM+s3Q='",
        "'sha256-ukGEpm76ZWGDlDStysCDbVRJgILWSgR1XiInXHpnqeo='",
        "'sha256-1pdWRQ5pLai42G3EWfkHyJXR4TFGVlzxJHpNF89iLTQ='",
        "'sha256-C8FeZKK7Sju/xx6ArM4j9W2/TcxCpb2IPSHJeqVK3hg='",
        "'sha256-/dNLhMcPPsv9gDusbsJ+xgTBKgl67iqN75nRsJwY1y8='",
        "'sha256-Fj+sWytTahUAg3Na/4zjY6QnSNhwgFsnz4JxbA2vzcw='",
        "'sha256-JCBsts/37Jx84rU5noLWawBDCAgz9kEjdmJQN3jBY8k='",
        "'sha256-04T2hHmvLBivvYNrvZCsJi3URODWHuMDbrtYi3CIfB4='",
        "'sha256-DC3munJ0pghuoA4hX8dh32935FOMe4Ek0lEToguPh04='",
        "'sha256-NDFP8wAl44R2n9vT1corxoEbvzy3cusyeGupfuQ1U0c='",
        "'sha256-PA1G79Xx6LLYGxSPHSieelZ8bBLAWIMgD/XXawZp7qU='",
        "'sha256-mCQxt+MP+ovw3u4TQgt01msH6eqt4mSVB0Qu2YWWMTg='",
        "'sha256-JvKBe3eX3y4VMRRoZ6gtD3NERM2ie6izqcfCYApav2Y='",
        "'sha256-TxuSliz/loxO7gZryrQvb0iCfYpUhvSaFj/6Td2gWFQ='",
        "'sha256-45pN/AJ0kQzJz9vwICzvV3MnuOG8gtGxggQwABWnymA='",
        "'sha256-obaP6XgYiPObVeZTvXdVlgt809T2Dm6PIk16JE30820='",
        "'sha256-X48Mhnt413YPDQKQ1WJRKySArZrDCn1RHfPwUz3f1n8='",
        "'sha256-4xP5qvZtoBaEfC9gZ43CQp8bEku+/CZOsq9FaRvF7OU='",
        "'sha256-mZcvwmv6hKtoYTrQMxgb/EQ337dAnjIahuJ3pleT24M='",
        "'sha256-DkOZu61D7CazmSXGaEnSn2z9djJ8MykUT8DxDGQdjbs='",
        "'sha256-DkOZu61D7CazmSXGaEnSn2z9djJ8MykUT8DxDGQdjbs='",
        "'sha256-rkLuhOrYkT+nja4WGqG4TPLui5JaWiPDYJJ8UCuslJw='",
        "'sha256-LvGubOm7HawnJzw+vOyACi6DYfal1wKpJYCE7KN/XDI='",
        "'sha256-5tQ8oYGMvQerAFL7X6FcoOun/fzsYLKwBeMevN0pth8='",
        "'sha256-wwXL5J3dFy1OlT0B3+GEak+gfFt97tLZtgA03Ww5uKU='",
        "'sha256-jZ0Oc9ZvtRDz3fu+52erC3krRmxFNM123/clxHqXT6I='",
        "'sha256-5SxuHuYxmlu7rNBznCkw0RTE+ONtAqVChmyV8gMsnyM='",
        "'sha256-fH3rM69L3MlQuLHwmENXZ9SSP9u+7mECRGOpE5pY/Hw='",
        "'sha256-7Xlpbhi2uHJajOb377ImeVoPP2wXatX9zj+Yr/DS0qA='",
        "'sha256-4rt4xlh501T8mF5LZkGs/NIyq3fs7igdd8csZexAN8I='",
        "'sha256-daEdpEyAJIa8b2VkCqSKcw8PaExcB6Qro80XNes/sHA='",
        "'sha256-j91bFxk70pyBgSjXdJizPOSoYZaC0Zt+fq9U4OF/npQ='",
        "'sha256-ZWirjyeue1OSyGpYxoRjbS2NRwKf/b/XZiYaHuUV6Wc='",
        "'sha256-rQJ6epAwyFQxC0sb4uq4sgIKJLr2jP19K4M0Bork7kM='",
        "'sha256-hH6THo5mChVoQ5wrDhew4wuTZxOayUnEJC3U1SK80VQ='",
        "'sha256-fUjKhLcjxDsHY0YkuZGJ9RcBu+3nIlSqpSUI9biHAJw='",
        "'sha256-7ydyyMhpPIo0fTHZtxmllQ+MJpMVM299EkUKAf0K1hs='",
    ],
    "style-src": [
        "self",
        "unsafe-inline",
        "*.googleapis.com",
        "*.bootstrapcdn.com",
        "*.datatables.net",
        "*.cloudflare.com ",
        "*.github.io"
        # "'sha256-eg/xnzXUz6KMG1HVuW/xUt76FyF5028DbB4i0AhZTjA='",
        # "'sha256-G/USJC1+tllSYwvERC+xNnfMa+5foeWVYBUWvwijyls='",
        # "'sha256-Z0H+TBASBR4zypo3RZbXhkcJdwMNyyMhi4QrwsslVeg='",
        # "'sha256-qxBJozwM44kf1mKAeiT/XkAwReBZ/To9FXKNw3bdVwk='"
    ],
    "img-src": [
        "self",
        "data:",
        "*.datatables.net",
        "*.googleapis.com",
        "*.gstatic.com",
        "*.google.com",
    ],
    "connect-src": ["self", "*.github.com"],
    "font-src": ["self", "*.gstatic.com", "*.bootstrapcdn.com"],
    "frame-src": ["self", "*.hydroshare.org"],
}


X_FRAME_OPTIONS = "deny"

SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_SECONDS = 31536000

# Cookie Stuff
SESSION_COOKIE_SECURE = USE_SECURITY
CSRF_COOKIE_SECURE = USE_SECURITY

# Categorization in discovery of content types
# according to file extension of otherwise unaggregated files.
DISCOVERY_EXTENSION_CONTENT_TYPES = {
    "Document": set(["doc", "docx", "pdf", "odt", "rtf", "tex", "latex"]),
    "Spreadsheet": set(["csv", "xls", "xlsx", "ods"]),
    "Presentation": set(["ppt", "pptx", "odp"]),
    "Jupyter Notebook": set(["ipynb"]),
    "Image": set(["gif", "jpg", "jpeg", "tif", "tiff", "png"]),
    "Multidimensional (NetCDF)": set(["nc"]),
}

HSWS_ACTIVATED = False

# HydroShare THREDDS Data Server URL
THREDDS_SERVER_URL = "https://thredds.hydroshare.org/thredds/"
# HydroShare Geoserver URL
HSWS_GEOSERVER_URL = "https://geoserver.hydroshare.org/geoserver"

# celery task names to be recorded in task notification model
TASK_NAME_LIST = [
    "hs_core.tasks.create_bag_by_irods",
    "hs_core.tasks.create_temp_zip",
    "hs_core.tasks.unzip_task",
    "hs_core.tasks.copy_resource_task",
    "hs_core.tasks.create_new_version_resource_task",
    "hs_core.tasks.delete_resource_task",
    "hs_core.tasks.move_aggregation_task",
]

####################################
# DO NOT PLACE SETTINGS BELOW HERE #
####################################

##################
# LOCAL SETTINGS #
##################

# Allow any settings to be defined in local_settings.py which should be
# ignored in your version control system allowing for settings to be
# defined per machine.
local_settings = __import__(local_settings_module, globals(), locals(), ["*"])
for k in dir(local_settings):
    locals()[k] = getattr(local_settings, k)

if 'test' in sys.argv:
    import logging

    logging.disable(logging.CRITICAL)
    PASSWORD_HASHERS = [
        'django.contrib.auth.hashers.MD5PasswordHasher',
    ]

####################
# DYNAMIC SETTINGS #
####################

# set_dynamic_settings() will rewrite globals based on what has been
# defined so far, in order to provide some better defaults where
# applicable. We also allow this settings module to be imported
# without Mezzanine installed, as the case may be when using the
# fabfile, where setting the dynamic settings below isn't strictly
# required.
try:
    from mezzanine.utils.conf import set_dynamic_settings
except ImportError:
    pass
else:
    set_dynamic_settings(globals())

####################
# Allow Unicode printout to terminals
####################
# import codecs
# sys.stdout = codecs.getwriter('utf8')(sys.stdout)
# sys.stderr = codecs.getwriter('utf8')(sys.stderr)

MODEL_PROGRAM_META_SCHEMA_TEMPLATE_PATH = (
    "/hydroshare/hs_file_types/model_meta_schema_templates"
)

BULK_UPDATE_CREATE_BATCH_SIZE = 1000

if ENABLE_OIDC_AUTHENTICATION:
    # The order of the authentication classes is important. The OIDC authentication class
    # see this issue: https://github.com/encode/django-rest-framework/issues/5865
    # The basic auth classes come first, then the session auth classes, then the OIDC and OAuth2 classes
    DEFAULT_AUTHENTICATION_CLASSES = ("hs_core.authentication.BasicOIDCAuthentication",) + \
        DEFAULT_AUTHENTICATION_CLASSES + ("mozilla_django_oidc.contrib.drf.OIDCAuthentication",)
    REST_FRAMEWORK["DEFAULT_AUTHENTICATION_CLASSES"] = DEFAULT_AUTHENTICATION_CLASSES
    AUTHENTICATION_BACKENDS.append("hs_core.authentication.HydroShareOIDCAuthenticationBackend")
