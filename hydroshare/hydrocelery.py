

import os

from celery import Celery
from django.conf import settings

# https://docs.celeryproject.org/en/latest/django/first-steps-with-django.html#using-celery-with-django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hydroshare.settings')
os.environ.setdefault('PYTHONPATH', '/hydroshare/hydroshare')

# ampq backend has been deprecated in celery v5
app = Celery('hydroshare', backend='rpc://', broker=settings.BROKER_URL)
app.config_from_object('django.conf:settings')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)


@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))
