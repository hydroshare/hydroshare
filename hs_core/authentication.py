from mozilla_django_oidc.auth import OIDCAuthenticationBackend
from hs_core.hydroshare import create_account
from django.urls import reverse, resolve


class HydroShareOIDCAuthenticationBackend(OIDCAuthenticationBackend):
    def create_user(self, claims):
        return create_account(
            email=claims.get('email', ''),
            username=claims.get('username', self.get_username(claims)),
            first_name=claims.get('given_name', ''),
            last_name=claims.get('family_name', ''),
            superuser=False,
            active=True,
            organization=claims.get('organization', ''),
            user_type=claims.get('user_type', ''),
            country=claims.get('country', ''),
            state=claims.get('state', ''))


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
