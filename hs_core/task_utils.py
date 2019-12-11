from celery.task.control import inspect


def _retrieve_job_id(res_id, job_dict, job_name='hs_core.tasks.create_bag_by_irods'):
    if job_dict:
        workers = job_dict.keys()
        for worker in workers:
            for job in job_dict[worker]:
                if job['name'] == job_name:
                    if res_id in job['args']:
                        return job['id']
    return None


def get_resource_bag_task(res_id):
    i = inspect()
    active_jobs = i.active()
    job_id = _retrieve_job_id(res_id, active_jobs)
    if not job_id:
        reserved_jobs = i.reserved()
        job_id = _retrieve_job_id(res_id, reserved_jobs)
        if not job_id:
            scheduled_jobs = i.scheduled()
            job_id = _retrieve_job_id(res_id, scheduled_jobs)

    return job_id
