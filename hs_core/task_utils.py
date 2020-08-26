from celery.task.control import inspect
from celery.result import AsyncResult
from celery.result import states
from django.conf import settings
from django.db import transaction

from hs_core.models import TaskNotification
from hs_core.hydroshare.utils import get_resource_by_shortkey
from hs_core.signals import post_delete_resource

import logging

logger = logging.getLogger('django')


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


def _retrieve_job_id(job_name, res_id):
    """
    Retrieve a job id corresponding to the job_name and match the res_id
    :param job_name: job name
    :param res_id: resource id
    :return: job id
    """
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
    task_ids = set()
    task_name_mapper = settings.TASK_NAME_MAPPING
    if job_dict:
        workers = list(job_dict.keys())
        for worker in workers:
            for job in job_dict[worker]:
                status = "progress" if queue_type == 'active' else "pending"
                payload = ''
                if 'args' in job and username in job['args']:
                    task_id = job['id']
                    task_list.append({
                        'id': task_id,
                        'name': task_name_mapper[job['name']],
                        'status': status,
                        'payload': payload
                    })
                    task_ids.add(job['id'])
                elif 'request' in job:
                    scheduled_job = job['request']
                    if 'args' in scheduled_job and username in scheduled_job['args']:
                        task_list.append({
                            'id': scheduled_job['id'],
                            'name': task_name_mapper[scheduled_job['name']],
                            'status': 'pending',
                            'payload': payload
                        })
                        task_ids.add(scheduled_job['id'])
    return task_list, task_ids


def create_task_notification(task_id, status='pending', name='', payload='', username=''):
    with transaction.atomic():
        obj, created = TaskNotification.objects.get_or_create(task_id=task_id,
                                                              defaults={'name': name,
                                                                        'payload': payload,
                                                                        'status': status,
                                                                        'username': username
                                                                        })
        if not created:
            if username:
                obj.username = username
            if name:
                obj.name = name
            if payload:
                obj.payload = payload
            obj.status = status
            obj.save()


def get_resource_bag_task(res_id):
    job_name = 'hs_core.tasks.create_bag_by_irods'
    return _retrieve_job_id(job_name, res_id)


def get_all_tasks(username):
    """
    get all tasks by a user identified by username input parameter
    :param username: the user to retrieve all tasks for
    :return: list of tasks where each task is a dict with id, name, and status keys
    """
    i = inspect()
    act_task_list, act_task_ids = _retrieve_user_tasks(username, i.active(), 'active')
    res_task_list, res_task_ids = _retrieve_user_tasks(username, i.reserved(), 'reserved')
    sched_task_list, sched_task_ids = _retrieve_user_tasks(username, i.scheduled(), 'scheduled')
    task_list = act_task_list + res_task_list + sched_task_list
    task_ids = act_task_ids.union(res_task_ids).union(sched_task_ids)
    task_notif_list = []
    for obj in TaskNotification.objects.filter(username=username):
        task_notif_list.append({
            'id': obj.task_id,
            'name': obj.name,
            'status': obj.status,
            'payload': obj.payload
        })
    task_list.extend(item for item in task_notif_list if item['id'] not in task_ids)
    return task_list


def get_task_by_id(task_id, name='', request=None):
    """
    get task dict by celery task id
    :param task_id: task id
    :param name: task name with default being empty
    :param payload: task payload to use. If empty, task return result will be used as payload
    :param request: the request object
    :return: task dict with keys id, name, status
    """
    result = AsyncResult(task_id)
    status = 'progress'
    username = request.user.username if request else ''
    if result.ready():
        try:
            ret_value = result.get()
            status = 'completed'
            create_task_notification(task_id=task_id, status='completed', name=name, username=username)
        # use the Broad scope Exception to catch all exception types since this function can be used for all tasks
        except Exception:
            # logging exception will log the full stack trace and prepend a line with the message str input argument
            logger.exception('An exception is raised from task {}'.format(task_id))
            status = 'failed'
    elif result.failed():
        status = 'failed'
    elif result.status == states.PENDING:
        status = 'pending'

    return {
        'id': task_id,
        'name': name,
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
        'status': 'aborted',
        'payload': ''
    }


def dismiss_task_by_id(task_id):
    """
    dismiss a celery task from TaskNotification model by task id
    :param task_id: task id
    :return: dismissed task dict
    """
    task_dict = {}
    filter_task = TaskNotification.objects.filter(task_id=task_id).first()
    if filter_task:
        task_dict = {
            'id': task_id,
            'name': filter_task.name,
            'status': filter_task.status,
            'payload': filter_task.payload
        }
        TaskNotification.objects.filter(task_id=task_id).delete()
    return task_dict


def set_task_delivered_by_id(task_id):
    """
    Set task to delivered status from TaskNotificatoin model by task id
    :param task_id: task id
    :return: dict of the task that has been set to the delivered status
    """
    task_dict = {}
    filter_task = TaskNotification.objects.filter(task_id=task_id).first()
    if filter_task:
        filter_task.status = 'delivered'
        filter_task.save()
        task_dict = {
            'id': task_id,
            'name': filter_task.name,
            'status': filter_task.status,
            'payload': filter_task.payload
        }
    return task_dict
