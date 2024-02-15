from urllib.parse import urlparse

import robot_detection
from ipware.ip import get_ip

from hs_tools_resource.models import (RequestUrlBase,
                                      RequestUrlBaseAggregation,
                                      RequestUrlBaseFile)


def get_client_ip(request):
    return get_ip(request)


def get_user_type(session):
    try:
        user = session.visitor.user
        usertype = user.userprofile.user_type
    except AttributeError:
        usertype = None
    return usertype


def get_user_email_domain(session):
    try:
        user = session.visitor.user
        emaildomain = user.email.split('@')[-1]
    except AttributeError:
        emaildomain = None
    return emaildomain


def get_user_email_tld(session, emaildomain=None):
    try:
        if not emaildomain:
            emaildomain = get_user_email_domain(session)
        if emaildomain:
            shortdomain = '.'.join(emaildomain.split('.')[1:])
            return shortdomain
    except AttributeError:
        return None


def is_human(user_agent):
    if robot_detection.is_robot(user_agent):
        return False
    return True


def get_std_log_fields(request, session=None):
    """ returns a standard set of metadata that to each receiver function.
    This ensures that all activities are reporting a consistent set of metrics
    """
    try:
        user_agent = request.headers['user-agent']
        human = is_human(user_agent)
    except KeyError:
        user_agent = None
        human = None
    user_type = None
    user_email_tld = None
    full_domain = None
    if session is not None:
        user_type = get_user_type(session)
        full_domain = get_user_email_domain(session)
        user_email_tld = get_user_email_tld(session, full_domain)

    return {
        'user_ip': get_client_ip(request),
        'user_type': user_type,
        'user_email_domain': user_email_tld,
        'user_email_domain_full': full_domain,
        'is_human': human,
        'user_agent': user_agent
    }


def authentic_redirect_url(url):
    """ Validates a url scheme and netloc is in an existing web app
    :param url: String of a url
    :return: Boolean, True if the url exists in a web app
    """
    if not url:
        return False
    u = urlparse(url)
    url_base = "{}://{}".format(u.scheme, u.netloc)
    return RequestUrlBase.objects.filter(value__startswith=url_base).exists() \
        or RequestUrlBaseAggregation.objects.filter(value__startswith=url_base).exists() \
        or RequestUrlBaseFile.objects.filter(value__startswith=url_base).exists()
