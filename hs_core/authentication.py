from mozilla_django_oidc.auth import OIDCAuthenticationBackend
from hs_core.hydroshare import create_account


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