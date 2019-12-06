from hs_core.hydroshare.utils import get_resource_by_shortkey
from celery.task.control import inspect


def get_resource_bag_task(res_id):
    i = inspect()
    active_jobs = i.active()
    if active_jobs:
        workers = active_jobs.keys()
        for worker in workers:
            for job in active_jobs[worker]:
                if job['name'] == 'hs_core.tasks.create_bag_by_irods':
                    if res_id in job['args']:
                        return job['id']
    # either there is no active job or the job for creating the resource bag has ended, so unlock the resource if
    # it is still locked for some reason
    res = get_resource_by_shortkey(res_id)
    if res.locked:
        res.locked = False
        res.save()
    return None
