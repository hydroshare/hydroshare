import hashlib
import hmac
import logging
import re
from typing import Optional, Tuple
from urllib.parse import quote, unquote

logger = logging.getLogger("hs_auth_proxy")


def parse_authorization_header(auth_header: str) -> Optional[dict]:
    """Parse AWS Signature V4 authorization header into its components."""
    if not auth_header:
        return None

    match = re.match(
        r'AWS4-HMAC-SHA256 Credential=([^,]+), SignedHeaders=([^,]+), Signature=(.+)',
        auth_header
    )

    if not match:
        return None

    credential = match.group(1)
    signed_headers = match.group(2)
    signature = match.group(3)

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


def get_s3_action_from_request(method: str, path: str, query_params: dict) -> str:
    """Map HTTP method, path, and query parameters to an S3 action string."""
    if 'uploads' in query_params:
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


def verify_signature_v4(
    method: str,
    path: str,
    headers: dict,
    query_params: dict,
    body: bytes,
    secret_key: str,
    auth_info: dict
) -> bool:
    """Verify AWS Signature Version 4 for the given request."""
    try:
        provided_signature = auth_info['signature']
        signed_headers_str = auth_info['signed_headers']
        date = auth_info['date']
        region = auth_info['region']
        service = auth_info['service']

        # Canonical request
        canonical_uri = quote(path, safe='/~')

        canonical_query_string = '&'.join(
            f"{quote(k, safe='~')}={quote(str(v), safe='~')}"
            for k, v in sorted(query_params.items())
        )

        signed_header_names = [h.strip() for h in signed_headers_str.split(';')]
        canonical_headers = []
        for header_name in signed_header_names:
            header_value = None
            for k, v in headers.items():
                if k.lower() == header_name:
                    header_value = v
                    break
            if header_value:
                header_value = ' '.join(header_value.split())
                canonical_headers.append(f"{header_name}:{header_value}")

        canonical_headers_str = '\n'.join(canonical_headers) + '\n'
        payload_hash = hashlib.sha256(body if body else b'').hexdigest()

        canonical_request = '\n'.join([
            method, canonical_uri, canonical_query_string,
            canonical_headers_str, signed_headers_str, payload_hash
        ])

        logger.debug(f"Canonical request:\n{canonical_request}")

        # String to sign
        algorithm = 'AWS4-HMAC-SHA256'
        credential_scope = f"{date}/{region}/{service}/aws4_request"
        canonical_request_hash = hashlib.sha256(canonical_request.encode('utf-8')).hexdigest()

        amz_date = None
        for k, v in headers.items():
            if k.lower() == 'x-amz-date':
                amz_date = v
                break

        if not amz_date:
            logger.warning("Missing x-amz-date header")
            return False

        string_to_sign = '\n'.join([
            algorithm, amz_date, credential_scope, canonical_request_hash
        ])

        logger.debug(f"String to sign:\n{string_to_sign}")

        # Signing key
        k_secret = ('AWS4' + secret_key).encode('utf-8')
        k_date = hmac.new(k_secret, date.encode('utf-8'), hashlib.sha256).digest()
        k_region = hmac.new(k_date, region.encode('utf-8'), hashlib.sha256).digest()
        k_service = hmac.new(k_region, service.encode('utf-8'), hashlib.sha256).digest()
        k_signing = hmac.new(k_service, b'aws4_request', hashlib.sha256).digest()

        # Signature
        calculated_signature = hmac.new(
            k_signing, string_to_sign.encode('utf-8'), hashlib.sha256
        ).hexdigest()

        logger.debug(f"Calculated signature: {calculated_signature}")
        logger.debug(f"Provided signature: {provided_signature}")

        return hmac.compare_digest(calculated_signature, provided_signature)

    except Exception as e:
        logger.error(f"Error verifying signature: {e}", exc_info=True)
        return False
