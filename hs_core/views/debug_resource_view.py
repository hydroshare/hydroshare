import json

from django.http import HttpResponse
from django.template import loader
from hs_core.views.utils import authorize, ACTION_TO_AUTHORIZE
from hs_access_control.models import PrivilegeCodes
from hs_core.tasks import resource_debug, get_non_preferred_paths
from django.shortcuts import redirect
from celery.result import AsyncResult


def debug_resource(request, shortkey):
    """ Debug view for resource depicts output of various integrity checking scripts """
    resource, _, _ = authorize(request, shortkey,
                               needed_permission=ACTION_TO_AUTHORIZE.VIEW_RESOURCE)

    template = loader.get_template('debug/debug_resource.html')
    context = {
        'shortkey': shortkey,
        'creator': resource.creator,
        'resource': resource,
        'raccess': resource.raccess,
        'owners': resource.raccess.owners,
        'editors': resource.raccess.get_users_with_explicit_access(PrivilegeCodes.CHANGE),
        'viewers': resource.raccess.get_users_with_explicit_access(PrivilegeCodes.VIEW),
        'public_AVU': resource.getAVU('isPublic'),
        'type_AVU': resource.getAVU('resourceType'),
        'modified_AVU': resource.getAVU('bag_modified'),
        'quota_holder': resource.quota_holder.username,
    }
    return HttpResponse(template.render(context, request))


def irods_issues(request, shortkey):
    """ Debug view for resource depicts output of various integrity checking scripts, runs async """
    resource, _, _ = authorize(request, shortkey,
                               needed_permission=ACTION_TO_AUTHORIZE.VIEW_RESOURCE)

    task = resource_debug.apply_async((resource.short_id,))
    return redirect("get_debug_task_status", task_id=task.task_id)


def check_task_status(request, task_id=None, *args, **kwargs):
    """Checks the task status of the resource_debug job specified by the task_id """
    if resource_debug.AsyncResult(task_id).ready():
        status = "SUCCESS"
        try:
            irods_issues, irods_errors, _ = AsyncResult(task_id).get()
        except Exception as e:
            status = "ERROR - {}".format(e)
        context = {
            'status': status,
            'irods_issues': irods_issues,
            'irods_errors': irods_errors,
        }
        return HttpResponse(json.dumps(context))
    else:
        return HttpResponse(json.dumps({"status": None,
                                        "state": AsyncResult(task_id).state}),
                            content_type="application/json")


def check_for_non_preferred_paths(request, shortkey):
    """Checks for non preferred file/folder paths in a given resource, runs async"""

    resource, _, _ = authorize(request, shortkey,
                               needed_permission=ACTION_TO_AUTHORIZE.VIEW_RESOURCE)
    task = get_non_preferred_paths.apply_async((resource.short_id,))
    return redirect("get_path_check_task_status", task_id=task.task_id)


def check_non_preferred_paths_task_status(request, task_id=None, *args, **kwargs):
    """Checks the status of the task/job that checks for non preferred path specified by the task_id """

    if get_non_preferred_paths.AsyncResult(task_id).ready():
        status = "SUCCESS"
        non_preferred_paths = []
        try:
            non_preferred_paths = AsyncResult(task_id).get()
        except Exception as e:
            status = "ERROR - {}".format(str(e))
        context = {
            "status": status,
            "non_preferred_paths": non_preferred_paths,
        }
        return HttpResponse(json.dumps(context))
    else:
        return HttpResponse(json.dumps({"status": None,
                                        "state": AsyncResult(task_id).state}),
                            content_type="application/json")
