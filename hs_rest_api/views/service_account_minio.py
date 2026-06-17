import logging
from datetime import timedelta

from django_s3.utils import bucket_and_zone
from drf_yasg import openapi
from rest_framework.views import APIView
from drf_yasg.utils import swagger_auto_schema
from rest_framework.response import Response
from knox.models import AuthToken
from rest_framework import status
from hs_core.models import get_user
from hs_core.views.utils import authorize, ACTION_TO_AUTHORIZE

logger = logging.getLogger(__name__)


class MinIOServiceAccounts(APIView):
    DEFAULT_EXPIRY_DAYS = 180

    @staticmethod
    def _build_access_key(username, service_account_key):
        return f"{username}:{service_account_key}"

    @staticmethod
    def _require_authenticated_user(request):
        if not request.user.is_authenticated:
            return None, Response({"detail": "Authentication credentials were not provided."},
                                  status=status.HTTP_401_UNAUTHORIZED)
        return get_user(request), None

    @classmethod
    def _get_expiry(cls, request):
        expiry_days = request.data.get("expiry", cls.DEFAULT_EXPIRY_DAYS)
        try:
            expiry_days = int(expiry_days)
        except (TypeError, ValueError):
            return None, Response({"detail": "expiry must be a positive integer (days)."},
                                  status=status.HTTP_400_BAD_REQUEST)

        if expiry_days <= 0:
            return None, Response({"detail": "expiry must be a positive integer (days)."},
                                  status=status.HTTP_400_BAD_REQUEST)

        return timedelta(days=expiry_days), None

    @swagger_auto_schema(
        operation_description="Creates a service account with access key/secret for the user. "
                              "Optional request field `expiry` sets token lifetime in days "
                              "(default: 180).",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "expiry": openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description="Optional token lifetime in days. Must be a positive integer.",
                    default=180,
                    minimum=1,
                )
            },
        ),
    )
    def post(self, request):
        user, unauthorized = self._require_authenticated_user(request)
        if unauthorized:
            return unauthorized

        expiry, invalid_expiry = self._get_expiry(request)
        if invalid_expiry:
            return invalid_expiry

        # Knox supports multiple service-account records per user.
        auth_token, _ = AuthToken.objects.create(user=user, expiry=expiry)
        response_json = {
            "access_key": self._build_access_key(user.username, auth_token.token_key),
            "secret_key": auth_token.digest,
            "created": auth_token.created,
            "expiry": auth_token.expiry,
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
                "created": token.created,
                "expiry": token.expiry,
            }
            for token in tokens
        ]
        return Response({"service_accounts": service_accounts}, status=status.HTTP_200_OK)


class MinIOServiceAccountsDelete(APIView):

    @staticmethod
    def _require_authenticated_user(request):
        if not request.user.is_authenticated:
            return None, Response({"detail": "Authentication credentials were not provided."},
                                  status=status.HTTP_401_UNAUTHORIZED)
        return get_user(request), None

    @swagger_auto_schema(operation_description="Delete a service account for the user")
    def delete(self, request, access_key):
        user, unauthorized = self._require_authenticated_user(request)
        if unauthorized:
            return unauthorized

        if ":" not in access_key:
            return Response(status=status.HTTP_404_NOT_FOUND)

        username, service_account_key = access_key.split(":", 1)
        if username != user.username:
            return Response(status=status.HTTP_404_NOT_FOUND)

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
