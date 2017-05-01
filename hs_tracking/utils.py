import robot_detection
from ipware.ip import get_ip


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
        shortdomain = '.'.join(emaildomain.split('.')[1:])
    except AttributeError:
        shortdomain = None
    return shortdomain


def is_human(user_agent):
    if robot_detection.is_robot(user_agent):
        return False
    return True


def get_std_log_fields(request, session=None):
    """ returns a standard set of metadata that to each receiver function.
    This ensures that all activities are reporting a consistent set of metrics
    """
    user_type = None
    user_email = None
    if session is not None:
        user_type = get_user_type(session)
        user_email = get_user_email_domain(session)

    return {
             'user_ip': get_client_ip(request),
             'user_type': user_type,
             'user_email_domain': user_email,
            }
