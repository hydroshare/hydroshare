from hydroshare.hydrocelery import app as celery_app
from celery.result import AsyncResult
from django.db import transaction

from hs_core.models import TaskNotification

import logging

logger = logging.getLogger('django')

celery_inspector = celery_app.control.inspect()


def _retrieve_task_id(job_name, res_id, job_dict):
    """
    internal function to retrieve a matching job id for job_name celery task (e.g., hs_core.tasks.create_bag_by_s3)
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
    active_jobs = celery_inspector.active()
    job_id = _retrieve_task_id(job_name, res_id, active_jobs)
    if not job_id:
        reserved_jobs = celery_inspector.reserved()
        job_id = _retrieve_task_id(job_name, res_id, reserved_jobs)
        if not job_id:
            scheduled_jobs = celery_inspector.scheduled()
            job_id = _retrieve_task_id(job_name, res_id, scheduled_jobs)
    return job_id


def get_task_user_id(request):
    if request.user.is_authenticated:
        return request.user.username
    return ""


def get_or_create_task_notification(task_id, status='progress', name='', payload='', username=''):
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
            if obj.status == 'progress':
                # only update status when it moves from progress, all others are finished states
                obj.status = status
            obj.save()

        return {
            'id': task_id,
            'name': name,
            'status': obj.status,
            'payload': obj.payload
        }


def get_task_notification(task_id):
    try:
        obj = TaskNotification.objects.get(task_id=task_id)

        return {
            'id': task_id,
            'name': obj.name,
            'status': obj.status,
            'payload': obj.payload
        }
    except TaskNotification.DoesNotExist:
        return None


def get_resource_bag_task(res_id):
    job_name = 'hs_core.tasks.create_bag_by_s3'
    return _retrieve_job_id(job_name, res_id)


def get_resource_delete_task(res_id):
    job_name = 'hs_core.tasks.delete_resource_task'
    return _retrieve_job_id(job_name, res_id)


def get_all_tasks(username):
    """
    get all tasks by a user identified by username input parameter
    :param username: the user to retrieve all tasks for
    :return: list of tasks where each task is a dict with id, name, and status keys
    """
    if not username:
        return []
    task_notif_list = []
    for obj in TaskNotification.objects.filter(username=username):
        task_notif_list.append({
            'id': obj.task_id,
            'name': obj.name,
            'status': obj.status,
            'payload': obj.payload
        })
    return task_notif_list


def revoke_task_by_id(task_id):
    """
    revoke a celery task by task id
    :param task_id: task id
    :return: aborted task dict
    """
    result = AsyncResult(task_id)
    result.revoke(terminate=True)
    filter_task = TaskNotification.objects.filter(task_id=task_id).first()
    if filter_task:
        filter_task.status = 'aborted'
        filter_task.save()
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
    Set task to delivered status from TaskNotification model by task id
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
