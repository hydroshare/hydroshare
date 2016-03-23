from .models import Session, Variable

class Tracking(object):
    """If a page implements "can_view(request)" we honor the permission and
    raise a 403 if the logged in user would normally not be able to view the
    content"""

    def process_request(self, request):
        session = Session.objects.for_request(request)
        session.record("visit", request.path)
