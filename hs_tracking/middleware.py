from .models import Session
import utils


class Tracking(object):
    """The default tracking middleware logs all successful responses as a 'visit' variable with
    the URL path as its value."""

    def process_response(self, request, response):

        # filter out heartbeat messages
        if request.path.startswith('/heartbeat/'):
            return response

        # filter out web crawlers
        user_agent = request.META.get('HTTP_USER_AGENT', None)
        if user_agent is None:
            return response
        elif not utils.is_human(user_agent):
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
        msg = ' '.join([str(item) for item in
                        ['user_ip=%s' % ip,
                         'http_method=%s' % request.method,
                         'http_code=%s' % response.status_code,
                         'user_type=%s' % usertype,
                         'user_email_domain=%s' % emaildomain,
                         'request_url=%s' % request.path]])

        # save the activity in the database
        session.record('visit', msg)

        return response
