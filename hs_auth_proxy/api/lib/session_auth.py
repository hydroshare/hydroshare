import base64
import json
import logging
import zlib
from datetime import datetime, timezone
from typing import Optional

from api.database import engine
from sqlalchemy import text

logger = logging.getLogger("hs_auth_proxy")


def get_user_from_token(username: str, token: str) -> Optional[tuple[str, int]]:
    """Validate a username/token pair and return (bucket_name, user_id) or None."""
    if not username or not token:
        return None

    logger.info(f"Validating token for username: {username}")

    query = """
    SELECT authtoken_token.key, authtoken_token.user_id
    FROM authtoken_token
    INNER JOIN auth_user ON authtoken_token.user_id = auth_user.id
    WHERE auth_user.username = :username
    """

    try:
        with engine.connect() as conn:
            result = conn.execute(text(query), parameters=dict(username=username))
            row = result.fetchone()

            if not row:
                logger.warning(f"No token found for username: {username}")
                return None

            stored_key, user_id = row

            if stored_key != token:
                logger.warning(f"Token mismatch for username: {username}")
                return None

            user_query = """
            SELECT theme_userprofile._bucket_name
            FROM theme_userprofile
            WHERE theme_userprofile.user_id = :user_id
            """
            result = conn.execute(text(user_query), parameters=dict(user_id=user_id))
            user_row = result.fetchone()

            if not user_row:
                logger.warning(f"Bucket name not found for user_id: {user_id}")
                return None

            bucket_name = user_row[0]
            logger.info(f"Token validated for user: {username} (bucket: {bucket_name})")
            return bucket_name, int(user_id)

    except Exception as e:
        logger.error(f"Database error validating token for {username}: {e}", exc_info=True)
        return None


def get_user_from_session(session_key: Optional[str]) -> Optional[tuple[str, int]]:
    """Validate a Django session key and return (bucket_name, user_id) or None."""
    if not session_key:
        return None

    logger.info(f"Validating session: {session_key[:10]}...")

    query = """
    SELECT session_data, expire_date
    FROM django_session
    WHERE session_key = :session_key
    """

    try:
        with engine.connect() as conn:
            result = conn.execute(text(query), parameters=dict(session_key=session_key))
            row = result.fetchone()

            if not row:
                logger.warning(f"Session not found: {session_key}")
                return None

            session_data, expire_date = row

            if expire_date.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
                logger.warning(f"Session expired: {session_key}")
                return None

            # Decode Django session: .<url_safe_base64_zlib_json>:<hash>
            try:
                encoded_data, _ = session_data.split(':', 1)

                if encoded_data.startswith('.'):
                    encoded_data = encoded_data[1:]

                missing_padding = len(encoded_data) % 4
                if missing_padding:
                    encoded_data += '=' * (4 - missing_padding)

                decoded_data = base64.urlsafe_b64decode(encoded_data.encode())
                decompressed_data = zlib.decompress(decoded_data)
                session_dict = json.loads(decompressed_data.decode('utf-8'))

                user_id = session_dict.get('_auth_user_id')
                if not user_id:
                    logger.warning(f"No user_id in session: {session_key}")
                    return None

                user_query = """
                SELECT auth_user.username, theme_userprofile._bucket_name
                FROM auth_user
                INNER JOIN theme_userprofile ON auth_user.id = theme_userprofile.user_id
                WHERE auth_user.id = :user_id
                """
                result = conn.execute(text(user_query), parameters=dict(user_id=user_id))
                user_row = result.fetchone()

                if not user_row:
                    logger.warning(f"User not found for id: {user_id}")
                    return None

                username, bucket_name = user_row
                logger.info(f"Session validated for user: {username} (bucket: {bucket_name})")
                return bucket_name, int(user_id)

            except Exception as e:
                logger.error(f"Error decoding session data: {e}", exc_info=True)
                return None

    except Exception as e:
        logger.error(f"Database error checking session: {e}", exc_info=True)
        return None
