__author__ = 'Pabitra'

from django.contrib.auth import authenticate
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import *
import serializers
from hs_core.views import utils

@api_view(['POST'])
def authenticate_user(request):
    """
    Authenticates a user based on username and password

    REST URL: /hsapi/authenticate

    HTTP method: POST

    HTTP status code (on success): 200

    :type username: str

    :type password: str

    :param username: username for the user to authenticate

    :param password: password for the user to authenticate

    :rtype: str

    :return: 'Authentication successful'

    :raises:

    &nbsp;&nbsp;&nbsp;ValidationError: return json format: {'username': ['error message-username'], 'password': ['error message-password']}

    &nbsp;&nbsp;&nbsp;HTTP status code:400

    &nbsp;&nbsp;&nbsp;PermissionDenied: return json format: {''detail': 'Incorrect authentication credentials.' }

    &nbsp;&nbsp;&nbsp;HTTP status code:403
    """

    user_authenticate_request_validator = serializers.UserAuthenticateRequestValidator(data=request.data)
    if not user_authenticate_request_validator.is_valid():
        raise ValidationError(detail=user_authenticate_request_validator.errors)

    user = authenticate(username=request.data['username'], password=request.data['password'])
    if user:
        return Response(data='Authentication successful', status=status.HTTP_200_OK)
    else:
        raise AuthenticationFailed()