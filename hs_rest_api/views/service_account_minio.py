import logging
from django_s3.utils import bucket_and_name
from rest_framework.views import APIView
from drf_yasg.utils import swagger_auto_schema
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework import status
from hs_core.models import get_user
from django.conf import settings
from hs_core.views.utils import authorize, ACTION_TO_AUTHORIZE

logger = logging.getLogger(__name__)

micro_auth_service_url = getattr(settings, 'MICRO_AUTH_SERVICE_URL', 'http://micro-auth/sa/auth/minio/sa/')


class MinIOServiceAccounts(APIView):

    @swagger_auto_schema(operation_description="Creates a service account with access key/secret for the user")
    def post(self, request):
        if not request.user.is_authenticated:
            return Response({"detail": "Authentication credentials were not provided."},
                            status=status.HTTP_401_UNAUTHORIZED)
        user = get_user(request)

        token, _ = Token.objects.get_or_create(user=user)
        response_json = {"access_key": user.username, "secret_key": token.key}
        return Response(response_json, status=201)

    @swagger_auto_schema(operation_description="Lists service accounts for the user")
    def get(self, request):
        raise NotImplementedError("Listing service accounts is not implemented yet.")


class MinIOServiceAccountsDelete(APIView):

    @swagger_auto_schema(operation_description="Delete a service account for the user")
    def delete(self, request, service_account_key):
        raise NotImplementedError("Deleting service accounts is not implemented yet.")


class MinIOResourceBucketAndPrefix(APIView):

    @swagger_auto_schema(operation_description="Retrieves the MinIO bucket and prefix for the resource")
    def get(self, request, pk):
        res, _, user = authorize(request, pk,
                                 needed_permission=ACTION_TO_AUTHORIZE.VIEW_RESOURCE)
        bucket, prefix = bucket_and_name(res.file_path + "/")
        return Response({"bucket": bucket, "prefix": prefix}, status=status.HTTP_200_OK)
