class SunsetMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        from django.utils.http import http_date
        from datetime import datetime

        response = self.get_response(request)
        auth = request.headers.get('Authorization')
        if not auth or 'Basic' not in auth:
            return response

        deprecation_date = datetime(2024, 4, 1)
        http_deprecation = http_date(deprecation_date.timestamp())
        help_link = "https://help.hydroshare.org/about-hydroshare/cuahsi-single-sign-on/"
        if datetime.now() > deprecation_date:
            response['Deprecation'] = http_deprecation
            response['Link'] = f'''<{help_link}>; rel="deprecation"; type="text/html"'''
        else:
            # https://datatracker.ietf.org/doc/html/rfc8594
            response['Sunset'] = http_deprecation
            response['Link'] = f'''<{help_link}>; rel="sunset"; type="text/html"'''
        return response
