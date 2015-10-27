from rest_framework.views import APIView
from rest_framework.response import Response


class UserInfo(APIView):
    def get(self, request):
        import logging
        logger = logging.getLogger('django')
        logger.debug(str(request.user))

        user_info = {"username": request.user.username}
        if request.user.email:
            user_info['email'] = request.user.email

        return Response(user_info)

