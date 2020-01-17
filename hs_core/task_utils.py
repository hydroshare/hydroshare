from celery.task.control import inspect


def _retrieve_task_id(res_id, job_dict):
    """
    internal function to retrieve a matching job id for create_bag_by_irods celery task from a specified celery
    job dictionary including active jobs, reserved jobs, and scheduled jobs. Active jobs and reserved jobs have the
    same dictionary format, while schedule jobs have a bit different format in which the job details are stored in the
    'request' key of a sub dictionary. Refer to
    http://docs.celeryproject.org/en/latest/userguide/workers.html?highlight=revoke#inspecting-workers for details.
    """
    job_name = 'hs_core.tasks.create_bag_by_irods'
    if job_dict:
        workers = list(job_dict.keys())
        for worker in workers:
            for job in job_dict[worker]:
                if 'name' in job:
                    if job['name'] == job_name:
                        if res_id in job['args']:
                            return job['id']
                elif 'request' in job:
                    scheduled_job = job['request']
                    if 'name' in scheduled_job:
                        if scheduled_job['name'] == job_name:
                            if res_id in scheduled_job['args']:
                                return scheduled_job['id']

    return None


def get_resource_bag_task(res_id):
    i = inspect()
    active_jobs = i.active()
    job_id = _retrieve_task_id(res_id, active_jobs)
    if not job_id:
        reserved_jobs = i.reserved()
        job_id = _retrieve_task_id(res_id, reserved_jobs)
        if not job_id:
            scheduled_jobs = i.scheduled()
            job_id = _retrieve_task_id(res_id, scheduled_jobs)

    return job_id
