import logging
from django.http import JsonResponse
from time import gmtime, strftime
from rest_framework.views import APIView

tlogger = logging.getLogger("django.timer")


class Timer(APIView):
    def get(self, request, function_name, uuid):
        '''
        Log the function that is being timed

        :param request:
        :param function_name: name of the function that is being timed
        :return: JSON response to return result
        '''
        here = strftime("%Y-%m-%d %H:%M:%S", gmtime())
        message = f"Starting call function {function_name} at {here} with UUID={uuid}"
        tlogger.info("*" * 50 + message + "*" * 50)
        return JsonResponse({"message": message})
