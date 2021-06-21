import os

from celery import Celery
from django.conf import settings

# https://docs.celeryproject.org/en/latest/django/first-steps-with-django.html#using-celery-with-django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hydroshare.settings')
os.environ.setdefault('PYTHONPATH', '/hydroshare/hydroshare')

app = Celery('hydroshare')
app.config_from_object('django.conf:settings')
# app.config_from_object('hydroshare.celeryconfig')  # can't do this, it resets the other get
app.conf.update(
    timezone='UTC', 
    enable_utc=True, 
    accept_content=['json'], 
    task_serializer='json', 
    result_serializer='json', 
    worker_hijack_root_logger=True, 
    task_default_exchange='tasks', 
    task_default_exchange_type='topic', 
    task_default_routing_key='task.default', 
    task_default_queue='default', 
    task_routes=('hs_core.router.HSTaskRouter',),
    broker_url=settings.BROKER_URL,
)

app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
# app.log.setup(logfile='/hydroshare/log/celery.log', loglevel='DEBUG') 
# app.log.setup_task_loggers(logfile='/hydroshare/log/defaultworker.log', loglevel='DEBUG') 
app.worker_hijack_root_logger = True

# LOGGING = {
#     'version': 1,
#     'disable_existing_loggers': True,
#     'formatters': {
#         'simple': {
#             'format': '%(levelname)s %(message)s',
#              'datefmt': '%y %b %d, %H:%M:%S',
#             },
#         },
#     'handlers': {
#         'console': {
#             'level': 'DEBUG',
#             'class': 'logging.StreamHandler',
#             'formatter': 'simple'
#         },
#         'celery': {
#             'level': 'DEBUG',
#             'class': 'logging.handlers.RotatingFileHandler',
#             'filename': 'celery.log',
#             'formatter': 'simple',
#             'maxBytes': 1024 * 1024 * 20,  # 20 mb
#         },
#         'defaultworker': {
#             'level': 'DEBUG',
#             'class': 'logging.handlers.RotatingFileHandler',
#             'filename': 'defaultworker.log',
#             'formatter': 'simple',
#             'maxBytes': 1024 * 1024 * 20,  # 20 mb
#         },
#     },
#     'loggers': {
#         'celery': {
#             'handlers': ['celery'],
#             'level': 'DEBUG',
#         },
#         'defaultworker': {
#             'handlers': ['defaultworker'],
#             'level': 'DEBUG',
#         },
#     }
# }
