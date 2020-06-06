from celery.task.control import inspect
from celery.result import AsyncResult
from celery.result import states
from django.conf import settings


def _retrieve_task_id(job_name, res_id, job_dict):
    """
    internal function to retrieve a matching job id for job_name celery task (e.g., hs_core.tasks.create_bag_by_irods)
    from a specified celery job dictionary including active jobs, reserved jobs, and scheduled jobs. Active jobs and
    reserved jobs have the same dictionary format, while schedule jobs have a bit different format in which the job
    details are stored in the 'request' key of a sub dictionary. Refer to
    http://docs.celeryproject.org/en/latest/userguide/workers.html?highlight=revoke#inspecting-workers for details.
    """
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


def _retrieve_user_tasks(username, job_dict, queue_type):
    """
    :param username: requesting user's username
    :param job_dict: celery job queue dict
    :param queue_type: type of job queue: active, reserved, or scheduled
    internal function to retrieve all tasks of a user identified by username input parameter from a specified celery
    job dictionary including active jobs, reserved jobs, and scheduled jobs.
    Active jobs and reserved jobs have the same dictionary format, while schedule jobs have a bit different format
    in which the job details are stored in the 'request' key of a sub dictionary. Refer to
    http://docs.celeryproject.org/en/latest/userguide/workers.html?highlight=revoke#inspecting-workers for details.
    """
    task_list = []
    task_name_mapper = settings.TASK_NAME_MAPPING
    if job_dict:
        workers = list(job_dict.keys())
        for worker in workers:
            for job in job_dict[worker]:
                status = "In progress" if queue_type == 'active' else "Pending execution"
                payload = ''
                if 'args' in job and username in job['args']:
                    task_id = job['id']
                    if queue_type == 'active':
                        result = AsyncResult(task_id)
                        if result.ready():
                            status = 'Completed'
                            payload = str(result.get()).lower()
                        elif result.failed():
                            status = 'Failed'
                    task_list.append({
                        'id': task_id,
                        'name': task_name_mapper[job['name']],
                        'status': status,
                        'payload': payload
                    })
                elif 'request' in job:
                    scheduled_job = job['request']
                    if 'args' in scheduled_job and username in scheduled_job['args']:
                        task_list.append({
                            'id': scheduled_job['id'],
                            'name': task_name_mapper[scheduled_job['name']],
                            'status': 'Pending execution',
                            'payload': payload
                        })
    return task_list


def get_resource_bag_task(res_id):
    job_name = 'hs_core.tasks.create_bag_by_irods'
    i = inspect()
    active_jobs = i.active()
    job_id = _retrieve_task_id(job_name, res_id, active_jobs)
    if not job_id:
        reserved_jobs = i.reserved()
        job_id = _retrieve_task_id(job_name, res_id, reserved_jobs)
        if not job_id:
            scheduled_jobs = i.scheduled()
            job_id = _retrieve_task_id(job_name, res_id, scheduled_jobs)

    return job_id


def get_all_tasks(username):
    """
    get all tasks by a user identified by username input parameter
    :param username: the user to retrieve all tasks for
    :return: list of tasks where each task is a dict with id, name, and status keys
    """
    i = inspect()
    act_task_lists = _retrieve_user_tasks(username, i.active(), 'active')
    res_task_lists = _retrieve_user_tasks(username, i.reserved(), 'reserved')
    sched_task_lists = _retrieve_user_tasks(username, i.scheduled(), 'scheduled')

    return act_task_lists + res_task_lists + sched_task_lists


def get_task_by_id(task_id):
    """
    get task dict by celery task id
    :param task_id: task id
    :return: task dict with keys id, name, status
    """
    result = AsyncResult(task_id)
    payload = ''
    status = 'In progress'
    if result.ready():
        status = 'Completed'
        payload = str(result.get()).lower()
    elif result.failed():
        status = 'Failed'
    elif result.status == states.PENDING:
        status = 'Pending execution'

    return {
        'id': task_id,
        'status': status,
        'payload': payload
    }


def revoke_task_by_id(task_id):
    """
    revoke a celery task by task id
    :param task_id: task id
    :return: aborted task dict
    """
    result = AsyncResult(task_id)
    result.revoke(terminate=True)
    return {
        'id': task_id,
        'status': 'Aborted',
        'payload': ''
    }
