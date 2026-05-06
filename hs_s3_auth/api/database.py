import base64
import json
import os
import zlib

from sqlalchemy import create_engine, text

DATABASE_URL = os.environ.get("HS_DATABASE_URL")
engine = create_engine(DATABASE_URL)


def quota_is_exceeded(resource_id: int):
    query = """SELECT (SELECT U0.exceeded
                       FROM theme_userquota U0
                       WHERE U0.user_id = (hs_core_genericresource.user_id) LIMIT 1) AS exceeded
               FROM hs_core_genericresource
               INNER JOIN pages_page
               ON (hs_core_genericresource.page_ptr_id = pages_page.id)
               WHERE hs_core_genericresource.short_id = :resource_id"""

    with engine.connect() as con:
        rs = con.execute(statement=text(query),
                         parameters=dict(resource_id=resource_id))
        row = rs.fetchone()
        if row:
            return row[0]
    return True


def get_user_token_and_id(username: str):
    # return (token_key, user_id) or None
    query = """SELECT authtoken_token.key, authtoken_token.user_id
    FROM authtoken_token
    INNER JOIN auth_user ON authtoken_token.user_id = auth_user.id
    WHERE auth_user.username = :username"""

    with engine.connect() as con:
        rs = con.execute(statement=text(query),
                         parameters=dict(username=username))
        row = rs.fetchone()
        if row:
            return row
    return None


def is_superuser_and_id(username: str):
    # return is_superuser and user_id as tuple
    query = """SELECT auth_user.is_superuser, theme_userprofile.user_id
    FROM auth_user
    INNER JOIN theme_userprofile
    ON auth_user.username = :username"""

    with engine.connect() as con:
        rs = con.execute(statement=text(query),
                         parameters=dict(username=username))
        row = rs.fetchone()
        if row:
            return row
    return {False, None}


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

    Handles two storage formats:
      - New (Django 2.0+): ``.{base64url_zlib_payload}:{timestamp}:{signature}``
      - Old             : ``base64({40-char-hash}:{json})``
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
    else:
        # Old format: standard base64(hash:json)
        padding = (4 - len(session_data) % 4) % 4
        decoded = base64.b64decode(session_data + '=' * padding)
        colon_idx = decoded.index(b':')
        return json.loads(decoded[colon_idx + 1:])


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
            return None
        session_data = row[0]

    try:
        session_dict = _decode_django_session_data(session_data)
    except Exception:
        return None

    raw_user_id = session_dict.get('_auth_user_id')
    if not raw_user_id:
        return None

    try:
        user_id = int(raw_user_id)
    except (ValueError, TypeError):
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
    return None
