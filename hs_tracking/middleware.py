from django.utils.deprecation import MiddlewareMixin

from .models import Session
from . import utils
import re

RESOURCE_RE = re.compile('resource/([0-9a-f]{32})/')  # parser for resource id
BAG_RE = re.compile('bags/([0-9a-f]{32})\.zip')  # parser for resource id # noqa
LANDING_RE = re.compile('resource/([0-9a-f]{32})/$')  # reference to resource home page
REST_RE = re.compile('/hsapi/')  # reference to REST or internal
INTERNAL_RE = re.compile('/hsapi/_internal/')  # reference to an internal page


def get_resource_id_from_url(path):
    """ read a resource id from a URL """
    m = RESOURCE_RE.search(path)
    if m and m.group(1):
        return m.group(1)
    m = BAG_RE.search(path)
    if m and m.group(1):
        return m.group(1)
    return None


def get_rest_from_url(path):
    """ determine whether a URL is a REST call or not

        This should always return boolean, not search result.
    """
    if REST_RE.search(path):
        if INTERNAL_RE.search(path):
            return False
        else:
            return True
    else:
        return False


def get_landing_from_url(path):
    """ determine whether a URL is a landing page.

        This should always return boolean, not search result.
    """
    if LANDING_RE.search(path):
        return True
    else:
        return False


class Tracking(MiddlewareMixin):
    """The default tracking middleware logs all successful responses as a 'visit' variable with
    the URL path as its value."""

    def process_response(self, request, response):

        # filter out heartbeat messages
        if request.path.startswith('/heartbeat/'):
            return response

        # filter out web crawlers
        is_human = getattr(request, 'is_human', False)
        if not is_human:
            return response

        # filter out everything that is not an OK response
        if response.status_code != 200:
            return response

        if not hasattr(request, 'user'):
            return response

        # get user info that will be recorded in the visit log
        session = Session.objects.for_request(request)
        usertype = utils.get_user_type(session)
        email_tld = utils.get_user_email_tld(session)
        ip = utils.get_client_ip(request)

        # build the message string (key:value pairs)
        msg = '|'.join([str(item) for item in
                        ['user_ip=%s' % ip,
                         'http_method=%s' % request.method,
                         'http_code=%s' % response.status_code,
                         'user_type=%s' % usertype,
                         'user_email_domain=%s' % email_tld,
                         'request_url=%s' % request.path]])

        resource_id = get_resource_id_from_url(request.path)
        rest = get_rest_from_url(request.path)
        landing = get_landing_from_url(request.path)

        # save the activity in the database
        session.record('visit', value=msg, resource_id=resource_id,
                       landing=landing, rest=rest)

        return response
