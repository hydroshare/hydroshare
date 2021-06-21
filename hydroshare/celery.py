import os

from celery import Celery
from django.conf import settings

# https://docs.celeryproject.org/en/latest/django/first-steps-with-django.html#using-celery-with-django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hydroshare.settings')
os.environ.setdefault('PYTHONPATH', '/hydroshare/hydroshare')

app = Celery('hydroshare')
app.config_from_object('django.conf:settings')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'simple': {
            'format': '%(levelname)s %(message)s',
             'datefmt': '%y %b %d, %H:%M:%S',
            },
        },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'celery': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'celery.log',
            'formatter': 'simple',
            'maxBytes': 1024 * 1024 * 20,  # 20 mb
        },
        'defaultworker': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'defaultworker.log',
            'formatter': 'simple',
            'maxBytes': 1024 * 1024 * 20,  # 20 mb
        },
    },
    'loggers': {
        'celery': {
            'handlers': ['celery'],
            'level': 'DEBUG',
        },
        'defaultworker': {
            'handlers': ['defaultworker'],
            'level': 'DEBUG',
        },
    }
}

@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))
