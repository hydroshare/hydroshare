from django.http import JsonResponse
from django.core.exceptions import RequestDataTooBig
from django.conf import settings
from hs_tools_resource.utils import convert_size
from django.urls import resolve


class CheckRequest():
    ''' Custom middleware to handle requests that exceed the DATA_UPLOAD_MAX_MEMORY_SIZE
    In this case, the request object might not have a body.
    This middleware creates the body and generages a more sensible response
    Related to https://code.djangoproject.com/ticket/29427
    '''
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            _ = request.body
        except RequestDataTooBig:
            view_name = resolve(request.path).view_name
            if view_name == "update_metadata_element":
                limit = convert_size(settings.DATA_UPLOAD_MAX_MEMORY_SIZE)
                return JsonResponse({"message": f"The upload was too big. Limit: {limit}"})
        return self.get_response(request)
