import logging
from typing import Optional, Tuple
from urllib.parse import unquote

logger = logging.getLogger("hs_s3_proxy")


def _get_query_param_case_insensitive(query_params: dict, key: str) -> Optional[str]:
    """Return query parameter value by key using case-insensitive key lookup."""
    key_lower = key.lower()
    for param_key, value in query_params.items():
        if str(param_key).lower() == key_lower:
            return value
    return None


def parse_authorization_header(auth_header: str) -> Optional[dict]:
    """Parse AWS Signature V4 authorization header into its components."""
    if not auth_header:
        return None

    prefix = 'AWS4-HMAC-SHA256 '
    if not auth_header.startswith(prefix):
        return None

    params_str = auth_header[len(prefix):]
    params = {}
    for part in params_str.split(','):
        part = part.strip()
        if '=' not in part:
            continue
        key, value = part.split('=', 1)
        params[key.strip()] = value.strip()

    credential = params.get('Credential')
    signed_headers = params.get('SignedHeaders')
    signature = params.get('Signature')

    if not all([credential, signed_headers, signature]):
        return None

    cred_parts = credential.split('/')
    if len(cred_parts) != 5:
        return None

    return {
        'algorithm': 'AWS4-HMAC-SHA256',
        'access_key': cred_parts[0],
        'date': cred_parts[1],
        'region': cred_parts[2],
        'service': cred_parts[3],
        'request_type': cred_parts[4],
        'signed_headers': signed_headers,
        'signature': signature
    }


def parse_presigned_auth_query(query_params: dict) -> Optional[dict]:
    """Parse SigV4 presigned query params into auth_info-compatible fields."""
    if not query_params:
        return None

    algorithm = _get_query_param_case_insensitive(query_params, 'X-Amz-Algorithm')
    credential = _get_query_param_case_insensitive(query_params, 'X-Amz-Credential')
    signed_headers = _get_query_param_case_insensitive(query_params, 'X-Amz-SignedHeaders')
    signature = _get_query_param_case_insensitive(query_params, 'X-Amz-Signature')

    if not all([algorithm, credential, signed_headers, signature]):
        return None

    if algorithm != 'AWS4-HMAC-SHA256':
        return None

    cred_parts = credential.split('/')
    if len(cred_parts) != 5:
        return None

    return {
        'algorithm': algorithm,
        'access_key': cred_parts[0],
        'date': cred_parts[1],
        'region': cred_parts[2],
        'service': cred_parts[3],
        'request_type': cred_parts[4],
        'signed_headers': signed_headers,
        'signature': signature,
    }


def get_s3_action_from_request(method: str, path: str, query_params: dict) -> str:
    """Map HTTP method, path, and query parameters to an S3 action string."""
    if 'uploads' in query_params:
        if method == 'POST':
            return 's3:CreateMultipartUpload'
        return 's3:ListMultipartUploadParts'
    if 'uploadId' in query_params:
        if method == 'POST':
            return 's3:CompleteMultipartUpload'
        elif method == 'DELETE':
            return 's3:AbortMultipartUpload'
        elif method == 'PUT':
            return 's3:UploadPart'
    if 'delete' in query_params:
        return 's3:DeleteObjects'
    if 'tagging' in query_params:
        if method == 'GET':
            return 's3:GetObjectTagging'
        elif method in ['PUT', 'POST']:
            return 's3:PutObjectTagging'
        elif method == 'DELETE':
            return 's3:DeleteObjectTagging'
    if 'acl' in query_params:
        if method == 'GET':
            return 's3:GetObjectAcl'
        elif method in ['PUT', 'POST']:
            return 's3:PutObjectAcl'
    if 'retention' in query_params:
        if method == 'GET':
            return 's3:GetObjectRetention'
        elif method in ['PUT', 'POST']:
            return 's3:PutObjectRetention'
    if 'legal-hold' in query_params:
        if method == 'GET':
            return 's3:GetObjectLegalHold'
        elif method in ['PUT', 'POST']:
            return 's3:PutObjectLegalHold'
    if 'location' in query_params:
        return 's3:GetBucketLocation'
    if 'object-lock' in query_params:
        return 's3:GetBucketObjectLockConfiguration'

    path_parts = [p for p in path.split('/') if p]

    if len(path_parts) == 0:
        if method == 'GET':
            return 's3:ListAllMyBuckets'
    elif len(path_parts) == 1:
        if method == 'GET':
            return 's3:ListBucket'
        elif method == 'PUT':
            return 's3:CreateBucket'
        elif method == 'DELETE':
            return 's3:DeleteBucket'
        elif method == 'HEAD':
            return 's3:HeadBucket'
    else:
        if method == 'GET':
            return 's3:GetObject'
        elif method == 'PUT':
            return 's3:PutObject'
        elif method == 'DELETE':
            return 's3:DeleteObject'
        elif method == 'HEAD':
            return 's3:HeadObject'
        elif method == 'POST':
            return 's3:PutObject'

    return 's3:Unknown'


def parse_s3_path(path: str) -> Tuple[Optional[str], Optional[str]]:
    """Parse S3 path into (bucket_name, object_key)."""
    path = unquote(path.lstrip('/'))

    if not path:
        return None, None

    parts = path.split('/', 1)
    bucket = parts[0] if parts else None
    object_key = parts[1] if len(parts) > 1 else None

    return bucket, object_key
