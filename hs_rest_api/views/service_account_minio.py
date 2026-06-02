import logging
from django_s3.utils import bucket_and_zone
from rest_framework.views import APIView
from drf_yasg.utils import swagger_auto_schema
from rest_framework.response import Response
from knox.models import AuthToken
from rest_framework import status
from hs_core.models import get_user
from django.conf import settings
from hs_core.views.utils import authorize, ACTION_TO_AUTHORIZE

logger = logging.getLogger(__name__)

hs_s3_auth_service_url = getattr(settings, 'HS_S3_AUTH_SERVICE_URL', 'http://hs-s3-auth/sa/auth/minio/sa/')


class MinIOServiceAccounts(APIView):

    @staticmethod
    def _build_access_key(username, service_account_key):
        return f"{username}:{service_account_key}"

    @staticmethod
    def _require_authenticated_user(request):
        if not request.user.is_authenticated:
            return None, Response({"detail": "Authentication credentials were not provided."},
                                  status=status.HTTP_401_UNAUTHORIZED)
        return get_user(request), None

    @swagger_auto_schema(operation_description="Creates a service account with access key/secret for the user")
    def post(self, request):
        user, unauthorized = self._require_authenticated_user(request)
        if unauthorized:
            return unauthorized

        # Knox supports multiple service-account records per user.
        auth_token, _ = AuthToken.objects.create(user=user)
        response_json = {
            "access_key": self._build_access_key(user.username, auth_token.token_key),
            "service_account_key": auth_token.token_key,
            "secret_key": auth_token.digest,
        }
        return Response(response_json, status=201)

    @swagger_auto_schema(operation_description="Lists service accounts for the user")
    def get(self, request):
        user, unauthorized = self._require_authenticated_user(request)
        if unauthorized:
            return unauthorized

        tokens = AuthToken.objects.filter(user=user).order_by('-created')
        service_accounts = [
            {
                "access_key": self._build_access_key(user.username, token.token_key),
                "service_account_key": token.token_key,
                "created": token.created,
                "expiry": token.expiry,
            }
            for token in tokens
        ]
        return Response({"service_accounts": service_accounts}, status=status.HTTP_200_OK)


class MinIOServiceAccountsDelete(APIView):

    @swagger_auto_schema(operation_description="Delete a service account for the user")
    def delete(self, request, service_account_key):
        if not request.user.is_authenticated:
            return Response({"detail": "Authentication credentials were not provided."},
                            status=status.HTTP_401_UNAUTHORIZED)

        user = get_user(request)
        deleted_count, _ = AuthToken.objects.filter(user=user, token_key=service_account_key).delete()
        if deleted_count == 0:
            return Response(status=status.HTTP_404_NOT_FOUND)

        return Response(status=status.HTTP_204_NO_CONTENT)


class MinIOResourceBucketAndPrefix(APIView):

    @swagger_auto_schema(operation_description="Retrieves the MinIO bucket and prefix for the resource")
    def get(self, request, pk):
        res, _, user = authorize(request, pk,
                                 needed_permission=ACTION_TO_AUTHORIZE.VIEW_RESOURCE)
        path = res.file_path + "/"
        bucket, zone = bucket_and_zone(path)
        return Response({"bucket": bucket, "prefix": path, "zone": zone}, status=status.HTTP_200_OK)
