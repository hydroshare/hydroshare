import logging
from django.http import JsonResponse
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.decorators import api_view

from hs_core.task_utils import get_task_notification

logger = logging.getLogger(__name__)


@swagger_auto_schema(method='get', auto_schema=None)
@api_view(['GET'])
def rest_check_task_status(request, task_id, *args, **kwargs):
    '''
    A REST view function to tell the client if the asynchronous create_bag_by_irods()
    task is done and the bag file is ready for download.
    Args:
        request: an ajax request to check for download status
    Returns:
        JSON response to return result from asynchronous task create_bag_by_irods
    '''
    if not task_id:
        task_id = request.POST.get('task_id')
    task_notification = get_task_notification(task_id)
    if task_notification:
        n_status = task_notification['status']
        if n_status in ['completed', 'delivered']:
            return JsonResponse({"status": 'true', 'payload': task_notification['payload']})
        if n_status == 'progress':
            return JsonResponse({"status": 'false'})
        if n_status in ['failed', 'aborted']:
            return JsonResponse({"status": 'false'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        return JsonResponse({"status": None})
