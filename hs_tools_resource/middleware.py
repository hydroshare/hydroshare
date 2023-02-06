from django.http import JsonResponse, HttpResponse
from django.core.exceptions import RequestDataTooBig
from django.conf import settings
from hs_tools_resource.utils import convert_size


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
            limit = convert_size(settings.DATA_UPLOAD_MAX_MEMORY_SIZE)
            return JsonResponse({"message": f"The upload was too big. Limit: {limit}"})

        response = self.get_response(request)
        return response

    def process_request(self, request):
        try:
            request.body
        except RequestDataTooBig as e:
            response = self.process_exception(request, e)
            if response is not None:
                return response
            else:
                pass

        return None

    def process_exception(self, request, exception):
        if isinstance(exception, RequestDataTooBig):
            return HttpResponse(status=413)
        return None
