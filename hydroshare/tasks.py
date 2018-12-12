from __future__ import absolute_import

from celery import Celery
from django.conf import settings

# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hydroshare.settings')
# os.environ.setdefault('PYTHONPATH', '/hydroshare/hydroshare')

# app = Celery('hydroshare', backend='amqp://')
app = Celery('hydroshare', backend='redis://redis:6379/0', broker='redis://redis:6379/0')
app.config_from_object('django.conf:settings')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)


@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))
