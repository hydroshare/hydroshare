

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
