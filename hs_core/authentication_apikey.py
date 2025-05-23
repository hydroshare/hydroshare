import logging

from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from rest_framework import authentication
from rest_framework import exceptions

logger = logging.getLogger(__name__)


class ApiKeyAuthentication(authentication.BaseAuthentication):
    """
    Custom authentication class for API key authentication.

    This class authenticates requests based on an API key provided in the request headers.
    The API key should be included in the 'X-API-KEY' header and must match the API_KEY
    defined in settings.
    """

    def authenticate(self, request):
        """
        Authenticate the request and return a tuple of (user, auth).

        Args:
            request: The request object

        Returns:
            A tuple of (None, True) if authentication is successful

        Raises:
            AuthenticationFailed: If the API key is missing or invalid
        """
        api_key = request.META.get('HTTP_X_API_KEY')
        if not api_key:
            raise exceptions.AuthenticationFailed('API key is required')

        # Get the API key from settings
        settings_api_key = getattr(settings, 'API_KEY', None)

        if not settings_api_key:
            logger.error("API_KEY is not defined in settings")
            raise exceptions.AuthenticationFailed('API key authentication is not configured')

        if api_key != settings_api_key:
            raise exceptions.AuthenticationFailed('Invalid API key')

        # Return AnonymousUser instead of None to avoid 'NoneType' has no attribute 'is_authenticated' errors
        return (AnonymousUser(), True)
