import base64
import json
import os
import zlib

from fastapi import logger

from sqlalchemy import create_engine, text

DATABASE_URL = os.environ.get("HS_DATABASE_URL")
engine = create_engine(DATABASE_URL)


def quota_is_exceeded(resource_id: int):
    query = """SELECT uq.exceeded
    FROM hs_core_genericresource gr
    JOIN theme_userquota uq
        ON uq.user_id = gr.quota_holder_id
    WHERE gr.short_id = :resource_id
    LIMIT 1"""

    with engine.connect() as con:
        rs = con.execute(statement=text(query),
                         parameters=dict(resource_id=resource_id))
        row = rs.fetchone()
        if row:
            return row[0]
    return True


def get_user_service_account_secrets_and_id(access_key: str):
    # return [(secret_key, user_id), ...]
    # Required access key format: <username>:<service_account_key>
    if ":" not in access_key:
        return []

    username, service_account_key = access_key.split(":", 1)
    query = """SELECT knox_authtoken.digest AS secret_key, knox_authtoken.user_id
    FROM knox_authtoken
    INNER JOIN auth_user ON knox_authtoken.user_id = auth_user.id
    WHERE auth_user.username = :username
    AND knox_authtoken.token_key = :service_account_key
    UNION ALL
    SELECT authtoken_token.key AS secret_key, authtoken_token.user_id
    FROM authtoken_token
    INNER JOIN auth_user ON authtoken_token.user_id = auth_user.id
    WHERE auth_user.username = :username
    AND authtoken_token.key = :service_account_key"""
    parameters = dict(username=username, service_account_key=service_account_key)

    with engine.connect() as con:
        rs = con.execute(statement=text(query),
                         parameters=parameters)
        rows = rs.fetchall()
        if rows:
            return rows
    return []


def is_superuser_and_id(username: str):
    # return is_superuser and user_id as tuple
    query = """SELECT auth_user.is_superuser, theme_userprofile.user_id
    FROM auth_user
    JOIN theme_userprofile ON theme_userprofile.user_id = auth_user.id
    WHERE auth_user.username = :username"""

    with engine.connect() as con:
        rs = con.execute(statement=text(query),
                         parameters=dict(username=username))
        row = rs.fetchone()
        if row:
            return row
    return False, None


def resource_discoverability(resource_id: str):
    # return public, allow_private_sharing, discoverable as tuple
    query = """SELECT hs_access_control_resourceaccess.public, hs_access_control_resourceaccess.allow_private_sharing,
        hs_access_control_resourceaccess.discoverable
    FROM hs_access_control_resourceaccess
    INNER JOIN hs_core_genericresource
    ON (hs_core_genericresource.page_ptr_id = hs_access_control_resourceaccess.resource_id)
    WHERE hs_core_genericresource.short_id = :resource_id"""

    with engine.connect() as con:
        rs = con.execute(statement=text(query),
                         parameters=dict(resource_id=resource_id))
        row = rs.fetchone()
        if row:
            return row
    return (False, False, False)


def user_has_view_access(user_id: int, resource_id: str):
    query = """SELECT DISTINCT hs_core_genericresource.short_id
    FROM hs_core_genericresource
    LEFT OUTER JOIN hs_access_control_userresourceprivilege
    ON (hs_core_genericresource.page_ptr_id = hs_access_control_userresourceprivilege.resource_id)
    LEFT OUTER JOIN hs_access_control_groupresourceprivilege
    ON (hs_core_genericresource.page_ptr_id = hs_access_control_groupresourceprivilege.resource_id)
    LEFT OUTER JOIN auth_group
    ON (hs_access_control_groupresourceprivilege.group_id = auth_group.id)
    LEFT OUTER JOIN hs_access_control_usergroupprivilege
    ON (auth_group.id = hs_access_control_usergroupprivilege.group_id)
    LEFT OUTER JOIN hs_access_control_groupaccess
    ON (auth_group.id = hs_access_control_groupaccess.group_id)
    INNER JOIN pages_page
    ON (hs_core_genericresource.page_ptr_id = pages_page.id)
    WHERE (hs_access_control_userresourceprivilege.user_id = :user_id
    OR (hs_access_control_usergroupprivilege.user_id = :user_id
    AND hs_access_control_groupaccess.active))
    AND hs_core_genericresource.short_id = :resource_id"""

    with engine.connect() as con:
        rs = con.execute(
            statement=text(query),
            parameters=dict(user_id=user_id, resource_id=resource_id),
        )
        result = rs.fetchone()
        if result:
            return True
        return False


def user_has_edit_access(user_id: int, resource_id: str):
    query = """SELECT DISTINCT hs_core_genericresource.short_id
    FROM hs_core_genericresource
    LEFT OUTER JOIN hs_access_control_userresourceprivilege
    ON (hs_core_genericresource.page_ptr_id = hs_access_control_userresourceprivilege.resource_id)
    LEFT OUTER JOIN hs_access_control_resourceaccess
    ON (hs_core_genericresource.page_ptr_id = hs_access_control_resourceaccess.resource_id)
    LEFT OUTER JOIN hs_access_control_groupresourceprivilege
    ON (hs_core_genericresource.page_ptr_id = hs_access_control_groupresourceprivilege.resource_id)
    LEFT OUTER JOIN auth_group
    ON (hs_access_control_groupresourceprivilege.group_id = auth_group.id)
    LEFT OUTER JOIN hs_access_control_usergroupprivilege
    ON (auth_group.id = hs_access_control_usergroupprivilege.group_id)
    LEFT OUTER JOIN hs_access_control_groupaccess
    ON (auth_group.id = hs_access_control_groupaccess.group_id)
    INNER JOIN pages_page
    ON (hs_core_genericresource.page_ptr_id = pages_page.id)
    WHERE ((hs_access_control_userresourceprivilege.privilege = 1
    AND hs_access_control_userresourceprivilege.user_id = :user_id)
    OR (hs_access_control_userresourceprivilege.privilege <= 2
    AND hs_access_control_userresourceprivilege.user_id = :user_id
    AND NOT hs_access_control_resourceaccess.immutable)
    OR (hs_access_control_usergroupprivilege.user_id = :user_id
    AND hs_access_control_groupaccess.active
    AND hs_access_control_groupresourceprivilege.privilege = 2
    AND NOT hs_access_control_resourceaccess.immutable))
    AND hs_core_genericresource.short_id = :resource_id"""
    with engine.connect() as con:
        rs = con.execute(
            statement=text(query),
            parameters=dict(user_id=user_id, resource_id=resource_id),
        )
        result = rs.fetchone()
        if result:
            return True
        return False


def _decode_django_session_data(session_data: str) -> dict:
    """Decode Django session data from the database.

    - (Django 2.0+): ``.{base64url_zlib_payload}:{timestamp}:{signature}``
    The HMAC signature is intentionally not verified here because the service
    already trusts the database; the expiry check in the SQL query is the
    security gate.
    """
    if session_data.startswith('.'):
        # New compressed format — payload precedes the first ':'
        payload_b64 = session_data.split(':', 1)[0][1:]  # strip leading '.'
        # Restore base64url padding
        padding = (4 - len(payload_b64) % 4) % 4
        payload_b64 += '=' * padding
        compressed = base64.urlsafe_b64decode(payload_b64)
        return json.loads(zlib.decompress(compressed))


def get_user_by_session_id(session_id: str):
    """Return ``(user_id, username)`` for a valid, non-expired Django session.

    Returns ``None`` if the session does not exist, has expired, or has no
    authenticated user.
    """
    session_query = """
        SELECT session_data
        FROM django_session
        WHERE session_key = :session_id
          AND expire_date > NOW()
    """
    with engine.connect() as con:
        rs = con.execute(statement=text(session_query), parameters=dict(session_id=session_id))
        row = rs.fetchone()
        if not row:
            logger.info(f"No valid session found for session_id={session_id}")
            return None
        session_data = row[0]

    try:
        session_dict = _decode_django_session_data(session_data)
    except Exception:
        logger.error(f"Error decoding session data for session_id={session_id}", exc_info=True)
        return None

    raw_user_id = session_dict.get('_auth_user_id')
    if not raw_user_id:
        return None

    try:
        user_id = int(raw_user_id)
    except (ValueError, TypeError):
        logger.error(f"Invalid user_id in session data for session_id={session_id}: {raw_user_id}", exc_info=True)
        return None

    user_query = """
        SELECT id, username
        FROM auth_user
        WHERE id = :user_id
    """
    with engine.connect() as con:
        rs = con.execute(statement=text(user_query), parameters=dict(user_id=user_id))
        row = rs.fetchone()
        if row:
            return row[0], row[1]
    logger.info(f"No valid user found for user_id={user_id}")
    return None
