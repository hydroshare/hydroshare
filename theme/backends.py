

from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.tokens import default_token_generator, PasswordResetTokenGenerator
from django.utils.http import base36_to_int, urlsafe_base64_decode
from six import text_type
from theme.utils import get_user_from_username_or_email


class WithoutLoggedInDateTokenGenerator(PasswordResetTokenGenerator):
    """
    Removes last_login from the hash of the PasswordResetTokenGenerator.  Allows use of generated tokens in scenarios
    where a user logging into their account after the token is generated should not expire the token
    """

    def _make_hash_value(self, user, timestamp):
        # override this method to remove last_login from hash
        return (
            text_type(user.pk) + user.password
            + text_type(timestamp)
        )


without_login_date_token_generator = WithoutLoggedInDateTokenGenerator()
User = get_user_model()


class CaseInsensitiveMezzanineBackend(ModelBackend):
    """
    Extends Django's ``ModelBackend`` to allow login via username,
    email, or verification token.  Username and email use a case insensitive query.
    Args are either ``username`` and ``password``, or ``uidb36``
    and ``token``. In either case, ``is_active`` can also be given.
    For login, is_active is not given, so that the login form can
    raise a specific error for inactive users.
    For password reset, True is given for is_active.
    For signup verficiation, False is given for is_active.
    """

    def authenticate(self, *args, **kwargs):
        if kwargs:
            username_or_email = kwargs.pop("username", None)
            if username_or_email:
                password = kwargs.pop("password", None)
                user = get_user_from_username_or_email(username_or_email, **kwargs)
                if user and user.check_password(password):
                    return user
            else:
                if 'uidb36' in kwargs:
                    kwargs["id"] = base36_to_int(kwargs.pop("uidb36"))
                elif 'uidb64' in kwargs:
                    # https://docs.djangoproject.com/en/3.2/releases/1.6/#django-contrib-auth-password-reset-uses-base-64-encoding-of-user-pk
                    uidb64 = kwargs.pop("uidb64")
                    kwargs["id"] = urlsafe_base64_decode(uidb64).decode()
                else:
                    return
                token = kwargs.pop("token")
                try:
                    user = User.objects.get(**kwargs)
                except User.DoesNotExist:
                    pass
                else:
                    if default_token_generator.check_token(user, token):
                        return user
                    elif without_login_date_token_generator.check_token(user, token):
                        return user
