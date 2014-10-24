import redis
import os

DEBUG = True

# Make these unique, and don't share it with anybody.
SECRET_KEY = "9e2e3c2d-8282-41b2-a027-de304c0bc3d944963c9a-4778-43e0-947c-38889e976dcab9f328cb-1576-4314-bfa6-70c42a6e773c"
NEVERCACHE_KEY = "7b205669-41dd-40db-9b96-c6f93b66123496a56be1-607f-4dbf-bf62-3315fb353ce6f12a7d28-06ad-4ef7-9266-b5ea66ed2519"

ALLOWED_HOSTS = "*"

REDIS_HOST = os.environ.get('REDIS_PORT_6379_TCP_ADDR', 'localhost')
REDIS_PORT = 6379
POSTGIS_HOST = os.environ.get('POSTGIS_PORT_5432_TCP_ADDR', 'localhost')
POSTGIS_PORT = 5432
POSTGIS_DB = os.environ.get('POSTGIS_DB', 'docker')
POSTGIS_PASSWORD = os.environ.get('POSTGIS_PASSWORD', 'docker')
POSTGIS_USER = os.environ.get('POSTGIS_USER', 'docker')

REDIS_CONNECTION = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=4)
WMS_CACHE_DB = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=5)
PERMISSIONS_DB= redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=6)


IPYTHON_SETTINGS=[]
IPYTHON_BASE='/home/docker/hydroshare/static/media/ipython-notebook'
IPYTHON_HOST='127.0.0.1'

# celery settings
BROKER_URL="redis://{REDIS_HOST}:6379/0".format(REDIS_HOST=REDIS_HOST)
CELERY_ACCEPT_CONTENT = ['pickle', 'json', 'msgpack', 'yaml']
CARTO_HOME='/home/docker/node_modules/carto'


USE_SOUTH = True
SITE_TITLE = "Hydroshare"

SESSION_EXPIRE_AT_BROWSER_CLOSE = True


#############
# DATABASES #
#############

DATABASES = {
    "default": {
        # Add "postgresql_psycopg2", "mysql", "sqlite3" or "oracle".
        "ENGINE": "django.contrib.gis.db.backends.postgis",
        # DB name or path to database file if using sqlite3.
        "NAME": POSTGIS_DB,
        # Not used with sqlite3.
        "USER": POSTGIS_USER,
        # Not used with sqlite3.
        "PASSWORD": POSTGIS_PASSWORD,
        # Set to empty string for localhost. Not used with sqlite3.
        "HOST": POSTGIS_HOST,
        # Set to empty string for default. Not used with sqlite3.
        "PORT": POSTGIS_PORT,
    }
}
POSTGIS_VERSION=(2,1,1)

HYDROSHARE_APPS = (
    "tastypie",
    "djcelery",
    "ga_ows",
    "ga_resources",
    "django_irods",
    "ga_interactive",
    "hs_core"
)


USE_IRODS=True
IRODS_ROOT='/tmp'
IRODS_ICOMMANDS_PATH='/usr/bin'
IRODS_HOST='data.hydroshare.org'
IRODS_PORT='1247'
IRODS_DEFAULT_RESOURCE='hydroResource'
IRODS_HOME_COLLECTION='/hydroZone/home/hssandbox'
IRODS_CWD='/hydroZone/home/hssandbox'
IRODS_ZONE='hydroZone'
IRODS_USERNAME='hssandbox'
IRODS_AUTH='sandboxwater1'
IRODS_GLOBAL_SESSION=True

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST_USER = 'hydroshare@hydroshare.org'
EMAIL_HOST_PASSWORD = 'zR=D~QBxU&}+'
EMAIL_HOST = 'gator3038.hostgator.com'
EMAIL_PORT = '26'
EMAIL_USE_TLS= True
DEFAULT_FROM_EMAIL= 'hydroshare@hydroshare.org'
