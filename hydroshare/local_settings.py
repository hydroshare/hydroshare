# DEVELOPMENT - local_settings.py
#    - This file should be copied to ~/hydroshare/hydroshare/local_settings.py
#    - The iRODS specific contents of this file contain username and password informaiton
#      that is used for a HydroShare proxy user

import redis
import os
from kombu import Queue, Exchange
from kombu.common import Broadcast

DEBUG = True

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
    Queue('default', routing_key='task.#'),
    Queue('docker_container_tasks', DOCKER_EXCHANGE, routing_key='docker.container'),
    Broadcast('docker_broadcast_tasks', DOCKER_EXCHANGE, routing_key='docker.broadcast'),
)
CELERY_DEFAULT_EXCHANGE = 'tasks'
CELERY_DEFAULT_EXCHANGE_TYPE = 'topic'
CELERY_DEFAULT_ROUTING_KEY = 'task.default'
CELERY_ROUTES = ('django_docker_processes.router.DockerRouter',)

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

# Email configuration
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
#EMAIL_HOST_USER = ''
#EMAIL_HOST_PASSWORD = ''
#EMAIL_HOST = ''
#EMAIL_PORT = ''
#EMAIL_USE_TLS = True
#DEFAULT_FROM_EMAIL = ''