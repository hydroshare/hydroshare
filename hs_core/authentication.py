import requests
import base64
from mozilla_django_oidc.auth import OIDCAuthenticationBackend
from hs_core.hydroshare import create_account
from django.urls import reverse, resolve
from django.conf import settings
from django.utils.http import urlencode
from django.contrib.auth.models import User
from rest_framework.authentication import BaseAuthentication
from keycloak.keycloak_openid import KeycloakOpenID


class HydroShareOIDCAuthenticationBackend(OIDCAuthenticationBackend):
    def create_user(self, claims):
        subject_areas = claims.get('subject_areas', '').split(";")
        return create_account(
            email=claims.get('email', ''),
            username=claims.get('preferred_username', self.get_username(claims)),
            first_name=claims.get('given_name', ''),
            last_name=claims.get('family_name', ''),
            superuser=False,
            active=claims.get('email_verified', True),
            organization=claims.get('organization', ''),
            user_type=claims.get('user_type', ''),
            country=claims.get('country', ''),
            state=claims.get('state', ''),
            subject_areas=subject_areas)


def build_oidc_url(request):
    """Builds a link to OIDC service
    To be called from within a view function

    Args:
        request: current request being processed by the view

    Returns:
        string: redirect URL for oidc service
    """
    view, args, kwargs = resolve(reverse('oidc_authentication_init'))
    kwargs["request"] = request
    redirect = view(*args, **kwargs)
    return redirect.url


def provider_logout(request):
    """ Create the user's OIDC logout URL."""
    # User must confirm logout request with the default logout URL
    # and is not redirected.
    logout_url = settings.OIDC_OP_LOGOUT_ENDPOINT
    redirect_url = settings.LOGOUT_REDIRECT_URL

    # If we have the oidc_id_token, we can automatically redirect
    # the user back to the application.
    oidc_id_token = request.session.get('oidc_id_token', None)
    if oidc_id_token:
        data = {
            "id_token_hint": oidc_id_token,
            "post_logout_redirect_uri": request.build_absolute_uri(
                location=redirect_url
            )
        }
        res = requests.post(logout_url, data)
        if not res.ok:
            logout_url = logout_url + "?" + urlencode(data)
        else:
            logout_url = redirect_url
    return logout_url


KEYCLOAK = KeycloakOpenID(
    server_url=settings.OIDC_KEYCLOAK_URL,
    client_id=settings.OIDC_RP_CLIENT_ID,
    realm_name=settings.OIDC_KEYCLOAK_REALM,
    client_secret_key=settings.OIDC_RP_CLIENT_SECRET,
)


class BasicOIDCAuthentication(BaseAuthentication):

    def authenticate(self, request):
        auth = request.headers.get('Authorization')
        if not auth or 'Basic' not in auth:
            return None
        _, value, *_ = request.headers.get('Authorization').split()

        decoded_username, decoded_password = (
            base64.b64decode(value).decode("utf-8").split(":")
        )
        # authenticate against keycloak
        try:
            KEYCLOAK.token(decoded_username, decoded_password)
        except Exception:
            return None

        user = User.objects.get(username=decoded_username)
        return (user, None)
