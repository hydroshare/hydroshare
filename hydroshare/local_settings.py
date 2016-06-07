# DEVELOPMENT - local_settings.py
#    - This file should be copied to ~/hydroshare/hydroshare/local_settings.py
#    - The iRODS specific contents of this file contain username and password informaiton
#      that is used for a HydroShare proxy user

import redis
import os
from kombu import Queue, Exchange
from kombu.common import Broadcast

DEBUG = True
TEMPLATE_DEBUG = True
# DEVELOPMENT EXAMPLE ONLY
# Make these unique, and don't share it with anybody
SECRET_KEY = "9e2e3c2d-8282-41b2-a027-de304c0bc3d944963c9a-4778-43e0-947c-38889e976dcab9f328cb-1576-4314-bfa6-70c42a6e773c"
NEVERCACHE_KEY = "7b205669-41dd-40db-9b96-c6f93b66123496a56be1-607f-4dbf-bf62-3315fb353ce6f12a7d28-06ad-4ef7-9266-b5ea66ed2519"

ALLOWED_HOSTS = "*"

# for Django/Mezzanine comments and ratings to require user login
COMMENTS_ACCOUNT_REQUIRED = True
RATINGS_ACCOUNT_REQUIRED = True
COMMENTS_USE_RATINGS = True

RABBITMQ_HOST = os.environ.get('RABBITMQ_PORT_5672_TCP_ADDR', 'localhost')
RABBITMQ_PORT = '5672'

REDIS_HOST = os.environ.get('REDIS_PORT_6379_TCP_ADDR', 'localhost')
REDIS_PORT = 6379
POSTGIS_HOST = os.environ.get('POSTGIS_PORT_5432_TCP_ADDR', 'localhost')
POSTGIS_PORT = 5432
POSTGIS_DB = os.environ.get('POSTGIS_DB', 'postgres')
POSTGIS_PASSWORD = os.environ.get('POSTGIS_PASSWORD', 'postgres')
POSTGIS_USER = os.environ.get('POSTGIS_USER', 'postgres')

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
# customizations: we need a special queue for broadcast signals to all
# docker daemons.  we also need a special queue for direct messages to all
# docker daemons.
BROKER_URL='amqp://guest:guest@{RABBITMQ_HOST}:{RABBITMQ_PORT}//'.format(RABBITMQ_HOST=RABBITMQ_HOST, RABBITMQ_PORT=RABBITMQ_PORT)
CELERY_ACCEPT_CONTENT = ['pickle', 'json', 'msgpack', 'yaml']
CELERY_DEFAULT_QUEUE = 'default'
DOCKER_EXCHANGE=Exchange('docker', type='direct')
DEFAULT_EXCHANGE=Exchange('default', type='topic')

CELERY_QUEUES = (
    Queue('default', DEFAULT_EXCHANGE, routing_key='task.default'),
    Queue('docker_container_tasks', DOCKER_EXCHANGE, routing_key='docker.container'),
    Broadcast('docker_broadcast_tasks', DOCKER_EXCHANGE, routing_key='docker.broadcast'),
)
CELERY_DEFAULT_EXCHANGE = 'tasks'
CELERY_DEFAULT_EXCHANGE_TYPE = 'topic'
CELERY_DEFAULT_ROUTING_KEY = 'task.default'
CELERY_ROUTES = ('hs_core.router.HSTaskRouter', 'django_docker_processes.router.DockerRouter',)

DOCKER_URL = 'unix://docker.sock/'
DOCKER_API_VERSION = '1.12'


# CartoCSS
CARTO_HOME='/home/docker/node_modules/carto'


USE_SOUTH = False
SITE_TITLE = "HydroShare"

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

# iRODS proxy user configuration
USE_IRODS = True
IRODS_ROOT = '/tmp'
IRODS_ICOMMANDS_PATH = '/usr/bin'
IRODS_HOST = 'hydrotest41.renci.org'
IRODS_PORT = '1247'
IRODS_DEFAULT_RESOURCE = 'hydrotest41Resc'
IRODS_HOME_COLLECTION = '/hydrotest41Zone/home/hsproxy'
IRODS_CWD = '/hydrotest41Zone/home/hsproxy'
IRODS_ZONE = 'hydrotest41Zone'
IRODS_USERNAME = 'hsproxy'
IRODS_AUTH = 'proxywater1'
IRODS_GLOBAL_SESSION = True

# iRODS customized bagit rule path
IRODS_BAGIT_RULE='hydroshare/irods/ruleGenerateBagIt_HS.r'
IRODS_BAGIT_PATH = 'bags'
IRODS_BAGIT_POSTFIX = 'zip'

# crossref login credential for resource publication
USE_CROSSREF_TEST = True
CROSSREF_LOGIN_ID = 'cuapi'
CROSSREF_LOGIN_PWD = 'fsd.38_C'

# Since Hyrax server on-demand update is only needed when private netCDF resources on www
# are made public, in local development environments or VM deployments other than the www
# production, this should not be run by setting RUN_HYRAX_UPDATE to False. RUN_HYRAX_UPDATE
# should only be set to True on www.hydroshare.org
RUN_HYRAX_UPDATE = False
HYRAX_SSH_HOST = "hyrax01.renci.org"
HYRAX_SSH_PROXY_USER = 'hsproxy'
HYRAX_SSH_PROXY_USER_PWD = '6hpRFC9!/ngr&{`ff}8Ye2t[`+Mj:g<t'
#HYRAX_SCRIPT_RUN_COMMAND = "sudo -u ihydroshare /opt/anaconda/bin/python /home/ihydroshare/scripts/expose_pub_netcdf_res.py"
HYRAX_SCRIPT_RUN_COMMAND = "sudo -u bes /usr/local/bin/python2.7 /var/log/bes/scripts/expose_pub_netcdf_res.py"

# hsuserproxy system user configuration used to create hydroshare iRODS users on-demand
HS_USER_ZONE_HOST = 'users.hydroshare.org'
HS_USER_ZONE_PROXY_USER = 'hsuserproxy'
HS_USER_ZONE_PROXY_USER_PWD = 'x/>r{7`tXm(MK$brqy@L>RB3CU@=Fv"@'
HS_USER_ZONE_PROXY_USER_CREATE_USER_CMD = '/home/hsuserproxy/create_user.sh'
HS_USER_ZONE_PROXY_USER_DELETE_USER_CMD = '/home/hsuserproxy/delete_user.sh'

# the local HydroShare proxy user (a counterpart of wwwHydroProxy) in a federated zone with HydroShare Zone
HS_LOCAL_PROXY_USER_IN_FED_ZONE = 'localTestHydroProxy'

# Please keep the line below unchanged since it is used to check whether
# the current site is in production or not
HS_WWW_IRODS_PROXY_USER = 'wwwHydroProxy'
# credentials for HydroShare proxy user iRODS account which is set to have own access control
# to all collections in any federated zone with HydroShare zone, which is only useful when testing HydroShare
# federated zone in local test development environment since in www production environment,
# IRODS_USERNAME and other associated settings already represent wwwHydroProxy settings
HS_WWW_IRODS_PROXY_USER_PWD = 'RmjYVeRnKj39vqAoTcAfpm7ksnoCxseh'
HS_WWW_IRODS_HOST = 'data.hydroshare.org'
HS_IRODS_LOCAL_ZONE_DEF_RES = 'hydroshareLocalResc'
HS_WWW_IRODS_ZONE = 'hydroshareZone'
HS_USER_IRODS_ZONE = 'hydroshareuserZone'

# Email configuration
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
#EMAIL_HOST_USER = 'hydroshare@hydroshare.org'
#EMAIL_HOST_PASSWORD = 'zR=D~QBxU&}+'
#EMAIL_HOST = 'gator3038.hostgator.com'
#EMAIL_PORT = '26'
#EMAIL_USE_TLS = True
DEFAULT_FROM_EMAIL = 'hydroshare@hydroshare.org'
DEFAULT_SUPPORT_EMAIL='hongyi@renci.org'

HYDROSHARE_SHARED_TEMP = '/shared_temp'
