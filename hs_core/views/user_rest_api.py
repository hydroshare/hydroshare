from rest_framework.views import APIView
from rest_framework.response import Response

from theme.models import UserProfile


class UserInfo(APIView):
    def get(self, request):
        user_profile = UserProfile.objects.filter(user=request.user).first()

        user_info = {"username": request.user.username}
        if request.user.email:
            user_info['email'] = request.user.email
        if request.user.first_name:
            user_info['first_name'] = request.user.first_name
        if request.user.id:
            user_info['id'] = request.user.id
        if user_profile.title:
            user_info['title'] = user_profile.title
        if user_profile.organization:
            user_info['organization'] = user_profile.organization
        if request.user.last_name:
            user_info['last_name'] = request.user.last_name

        return Response(user_info)

