

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[-1].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_user_type(session):
    user = session.visitor.user
    usertype = 'None'
    if user is not None:
        usertype = user.userprofile.user_type or 'undefined'
    return usertype


def get_user_email_domain(session):
    user = session.visitor.user
    emaildomain = 'None'
    if user is not None:
        emaildomain = user.email.split('.')[-1]
    return emaildomain
