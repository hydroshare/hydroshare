import datetime

from celery import group
from celery.task import periodic_task, task
from celery.schedules import crontab
from .models import DataResource
from django.utils.timezone import utc


#@task(ignore_result=True)
def refresh_resource(pk):
    """
    This is an asynchronous task that wraps the refresh method on a resource so it can be done asynchonously

    :return:
    """
    r = DataResource.get(pk=pk)
    try:
        r.modified()
        r.driver_instance.compute_fields()
        if hasattr(r.driver_instance, 'as_dataframe'):
            k = r.dataframe # force the generationg of the canonical dataframe object
    except:
        print "cannot refresh {s} ({r})".format(s=r.slug, r=r.title) # fixme this should be a log message

    now = datetime.datetime.utcnow().replace(tzinfo=utc)
    nxt = now + r.refresh_every
    r.last_refresh = now
    r.next_refresh = nxt
    r.save()


#@periodic_task(ignore_result=True, run_every=crontab(minute='*/15'))
def refresh_resources():
    """
    This is an asynchronous task that refreshes all the resources in the database who need refreshing.

    :return:
    """
    now = datetime.datetime.utcnow().replace(tzinfo=utc)
    res = DataResource.objects.filter(next_refresh__lte=now)
    task_grp = [refresh_resource.s(r.pk) for r in res]
    if task_grp:
       task_grp = group(task_grp)
       task_grp.apply_async().get()

#@task(ignore_result=True)
def data_resource_compute_fields(pk):
    ds = DataResource.objects.get(pk=pk)
    ds.driver_instance.compute_fields()
    if hasattr(ds.driver_instance, 'as_dataframe'):
        k = ds.dataframe # force the generationg of the canonical dataframe object
