from rest_framework.views import APIView
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema

from theme.models import UserProfile
from hs_core.views import serializers


class UserInfo(APIView):
    @swagger_auto_schema(operation_description="Get information about the logged in user",
                         responses={200: serializers.UserInfoSerializer})
    def get(self, request):
        '''
        Get information about the logged in user

        :param request:
        :return: HttpResponse response containing **user_info**
        '''
        if not request.user.is_authenticated:
            return Response({"title": "None", "organization": "None", "state": "None", "country": "None",
                             "user_type": "None"})

        user_info = {"username": request.user.username}

        if request.user.email:
            user_info['email'] = request.user.email
        if request.user.first_name:
            user_info['first_name'] = request.user.first_name
        if request.user.id:
            user_info['id'] = request.user.id
        if request.user.last_name:
            user_info['last_name'] = request.user.last_name

        user_profile = UserProfile.objects.filter(user=request.user).first()
        if user_profile.title:
            user_info['title'] = user_profile.title
        if user_profile.organization:
            user_info['organization'] = user_profile.organization
        if user_profile.state and user_profile.state.strip() and user_profile.state != 'Unspecified':
            user_info['state'] = user_profile.state.strip()
        if user_profile.country and user_profile.country != 'Unspecified':
            user_info['country'] = user_profile.country
        if user_profile.user_type and user_profile.user_type.strip() and user_profile.user_type != 'Unspecified':
            user_info['user_type'] = user_profile.user_type.strip()
        return Response(user_info)
