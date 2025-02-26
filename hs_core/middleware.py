from django.http import HttpResponse
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin


class HSClientMiddleware(MiddlewareMixin):
    """Default middleware for checking if a request is made from deprecated versions of hsclient

    HS>3.0 is only compatible with hsclient>=1.1.6
    The version of hsclient is passed in the user agent request header
    """

    def process_response(self, request, response):
        # https://github.com/hydroshare/hsclient/blob/1.1.6/hsclient/hydroshare.py#L1331
        # if a request is made from hsclient, it should contain a user-agent header like '... (hsclient 1.1.6)'
        if 'hsclient' in request.META.get('HTTP_USER_AGENT', ''):
            # parse the version number from the user-agent header
            request_version_string = '0.0.0'
            try:
                # extract the version number from the user-agent header
                request_version_string = request.META.get('HTTP_USER_AGENT', '').split('hsclient ')[1].split(')')[0]
            except IndexError:
                pass
            # check if the version is less than allowed version
            min_version_string = getattr(settings, 'HSCLIENT_MIN_VERSION', '1.1.6')
            min_version = tuple(map(int, min_version_string.split('.')))
            request_version = tuple(map(int, request_version_string.split('.')))
            if request_version < min_version:
                response = HttpResponse(status=400)
                message = f'Version {request_version_string} is deprecated. \
                    Please upgrade hsclient to version {min_version_string} or later'
                response.content = message
        return response
