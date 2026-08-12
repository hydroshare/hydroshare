import hashlib
import hmac
import logging
from urllib.parse import quote

logger = logging.getLogger("micro-auth")


def verify_signature_v4(
    method: str,
    path: str,
    headers: dict,
    query_params: dict,
    payload_hash: str,
    secret_key: str,
    auth_info: dict,
) -> bool:
    """Verify AWS Signature Version 4 given a precomputed payload hash."""
    try:
        provided_signature = auth_info['signature']
        signed_headers_str = auth_info['signed_headers']
        date = auth_info['date']
        region = auth_info['region']
        service = auth_info['service']

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

        canonical_request = '\n'.join([
            method, canonical_uri, canonical_query_string,
            canonical_headers_str, signed_headers_str, payload_hash,
        ])

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
            algorithm, amz_date, credential_scope, canonical_request_hash,
        ])

        k_secret = ('AWS4' + secret_key).encode('utf-8')
        k_date = hmac.new(k_secret, date.encode('utf-8'), hashlib.sha256).digest()
        k_region = hmac.new(k_date, region.encode('utf-8'), hashlib.sha256).digest()
        k_service = hmac.new(k_region, service.encode('utf-8'), hashlib.sha256).digest()
        k_signing = hmac.new(k_service, b'aws4_request', hashlib.sha256).digest()

        calculated_signature = hmac.new(
            k_signing, string_to_sign.encode('utf-8'), hashlib.sha256,
        ).hexdigest()

        return hmac.compare_digest(calculated_signature, provided_signature)

    except Exception as e:
        logger.error(f"Error verifying signature: {e}", exc_info=True)
        return False
