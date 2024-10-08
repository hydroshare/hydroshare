import gdown
import tempfile
import os
import logging
from rest_framework.views import APIView
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework import status
from hs_core.task_utils import get_or_create_task_notification, get_task_user_id
from hs_core.tasks import download_and_ingest_drive_file

from hs_core.views.utils import authorize, ACTION_TO_AUTHORIZE

from hs_core.management.utils import ingest_irods_files
from django.http import JsonResponse


logger = logging.getLogger(__name__)


class LargeFileGDrive(APIView):

    @swagger_auto_schema(
        operation_description="Downloads a google drive shareable link to a resource",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'shareable_link': openapi.Schema(type=openapi.TYPE_STRING, description='Google Drive shareable link'),
                'resource_relative_file_path': openapi.Schema(type=openapi.TYPE_STRING, description='Relative file path in the resource'),
            },
            required=['shareable_link', 'resource_relative_file_path']
        )
    )
    def post(self, request, pk):
        shareable_link = request.data.get('shareable_link')
        resource_relative_file_path = request.data.get('resource_relative_file_path')

        if not shareable_link or not resource_relative_file_path:
            return Response({"error": "Missing required parameters."}, status=status.HTTP_400_BAD_REQUEST)

        resource, _, _ = authorize(request, pk,
                                 needed_permission=ACTION_TO_AUTHORIZE.EDIT_RESOURCE)
        
        full_file_path = os.path.join(resource.file_path, resource_relative_file_path)
        task = download_and_ingest_drive_file.apply_async((shareable_link, full_file_path))
        task_dict = get_or_create_task_notification(task.task_id, name='gdrive download', payload="",
                                                    username=get_task_user_id(request))
        return JsonResponse(task_dict)
