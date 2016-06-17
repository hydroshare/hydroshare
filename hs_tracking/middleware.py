from .models import Session


class Tracking(object):
    """The default tracking middleware logs all successful responses as a 'visit' variable with
    the URL path as its value."""

    def process_response(self, request, response):
        if response.status_code == 200:
            session = Session.objects.for_request(request)
            session.record("visit", request.path)
        return response
