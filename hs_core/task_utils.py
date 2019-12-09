from celery.task.control import inspect


def get_resource_bag_task(res_id):
    i = inspect()
    active_jobs = i.active()
    reserved_jobs = i.reserved()
    scheduled_jobs = i.scheduled()
    if active_jobs:
        workers = active_jobs.keys()
        for worker in workers:
            for job in active_jobs[worker]:
                if job['name'] == 'hs_core.tasks.create_bag_by_irods':
                    if res_id in job['args']:
                        return job['id']
    if reserved_jobs:
        workers = reserved_jobs.keys()
        for worker in workers:
            for job in reserved_jobs[worker]:
                if job['name'] == 'hs_core.tasks.create_bag_by_irods':
                    if res_id in job['args']:
                        return job['id']
    if scheduled_jobs:
        workers = scheduled_jobs.keys()
        for worker in workers:
            for job in scheduled_jobs[worker]:
                if job['name'] == 'hs_core.tasks.create_bag_by_irods':
                    if res_id in job['args']:
                        return job['id']
    return None
