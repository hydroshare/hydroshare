import robot_detection


def get_client_ip(request):
    try:
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[-1].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
    except AttributeError:
        ip = None
    return ip


def get_user_type(session):
    try:
        user = session.visitor.user
        usertype = user.userprofile.user_type or 'undefined'
    except AttributeError:
        usertype = None
    return usertype


def get_user_email_domain(session):
    try:
        user = session.visitor.user
        emaildomain = user.email.split('.')[-1]
    except AttributeError:
        emaildomain = None
    return emaildomain


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
