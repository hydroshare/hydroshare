from .models import Session
import utils
import re

RESOURCE_RE = re.compile('resource/([0-9a-f]{32})/')


def get_resource_id_from_url(request):

    m = RESOURCE_RE.search(request)
    if (m and m.group(1)):
        resource_id = m.group(1)
        return resource_id
    else:
        return None


class Tracking(object):
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

        # get user info that will be recorded in the visit log
        session = Session.objects.for_request(request)
        usertype = utils.get_user_type(session)
        emaildomain = utils.get_user_email_domain(session)
        ip = utils.get_client_ip(request)

        # build the message string (key:value pairs)
        msg = '|'.join([str(item) for item in
                        ['user_ip=%s' % ip,
                         'http_method=%s' % request.method,
                         'http_code=%s' % response.status_code,
                         'user_type=%s' % usertype,
                         'user_email_domain=%s' % emaildomain,
                         'request_url=%s' % request.path]])

        resource_id = get_resource_id_from_url(request.path)

        # save the activity in the database
        session.record('visit', value=msg, resource_id=resource_id)

        return response
