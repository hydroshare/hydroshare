from rest_framework.views import APIView
from rest_framework.response import Response


class UserInfo(APIView):
    def get(self, request):
        user_info = {"username": request.user.username}
        if request.user.email:
            user_info['email'] = request.user.email
        if request.user.first_name:
            user_info['first_name'] = request.user.first_name
        if request.user.last_name:
            user_info['last_name'] = request.user.last_name

        return Response(user_info)

