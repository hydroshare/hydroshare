import logging

from api.lib.auth_service import check_authorization_sync

logger = logging.getLogger("hs_s3_proxy")


def check_s3_authorization(username: str, action: str, bucket: str, object_path: str) -> bool:
    if not action.startswith("s3:"):
        action = f"s3:{action}"

    prefixes = [object_path] if object_path else []

    return check_authorization_sync(
        username=username,
        action=action,
        bucket=bucket,
        object_path=object_path,
        prefixes=prefixes
    )
