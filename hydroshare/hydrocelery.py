

import os

from celery import Celery
from celery.signals import worker_process_init
from django.conf import settings
from opentelemetry.instrumentation.celery import CeleryInstrumentor

# https://docs.celeryproject.org/en/latest/django/first-steps-with-django.html#using-celery-with-django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hydroshare.settings')
os.environ.setdefault('PYTHONPATH', '/hydroshare/hydroshare')


@worker_process_init.connect(weak=False)
def init_celery_tracing(*args, **kwargs):
    CeleryInstrumentor().instrument()


# ampq backend has been deprecated in celery v5
app = Celery('hydroshare', backend='rpc://', broker=settings.BROKER_URL)
app.config_from_object('django.conf:settings')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

# https://docs.celeryq.dev/en/v5.2.7/userguide/routing.html#routing-automatic
app.conf.task_default_queue = 'default'
app.conf.task_create_missing_queues = True

# create router for celery tasks, to separate periodic tasks from other tasks
app.conf.task_routes = {
    'hydroshare.tasks.periodic': {'queue': 'periodic'},
}


@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))
