import hashlib
import hmac
import logging
from urllib.parse import quote

logger = logging.getLogger("hs-s3-auth")


def _uri_encode(value: str) -> str:
    # SigV4 canonical encoding (RFC3986): keep only unreserved characters.
    return quote(str(value), safe='-_.~')


def _canonical_query_string(query_params: dict) -> str:
    encoded_pairs = []
    for key, value in query_params.items():
        if str(key).lower() == "x-amz-signature":
            continue
        encoded_pairs.append((_uri_encode(key), _uri_encode(value)))
    encoded_pairs.sort(key=lambda pair: (pair[0], pair[1]))
    return '&'.join(f"{k}={v}" for k, v in encoded_pairs)


def _host_variants(headers: dict) -> list[dict]:
    variants = []
    base = dict(headers)
    variants.append(base)

    x_forwarded_host = base.get('x-forwarded-host')
    if x_forwarded_host:
        original_host = x_forwarded_host.split(',')[0].strip()
        if original_host:
            forwarded_host_variant = dict(base)
            forwarded_host_variant['host'] = original_host
            variants.append(forwarded_host_variant)

            x_forwarded_port = base.get('x-forwarded-port', '').strip()
            if x_forwarded_port and ':' not in original_host:
                with_port_variant = dict(base)
                with_port_variant['host'] = f"{original_host}:{x_forwarded_port}"
                variants.append(with_port_variant)

    x_original_host = base.get('x-original-host', '').strip()
    if x_original_host:
        original_variant = dict(base)
        original_variant['host'] = x_original_host
        variants.append(original_variant)

    return variants


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
        normalized_headers = {str(k).lower(): str(v) for k, v in headers.items()}

        provided_signature = auth_info['signature']
        signed_headers_str = auth_info['signed_headers']
        date = auth_info['date']
        region = auth_info['region']
        service = auth_info['service']

        canonical_uri = quote(path, safe='/-_.~')
        canonical_query_string = _canonical_query_string(query_params)

        signed_header_names = [h.strip() for h in signed_headers_str.split(';')]
        algorithm = 'AWS4-HMAC-SHA256'
        credential_scope = f"{date}/{region}/{service}/aws4_request"

        amz_date = normalized_headers.get('x-amz-date')

        # Presigned URLs carry x-amz-date in query params rather than headers.
        if not amz_date:
            for k, v in query_params.items():
                if str(k).lower() == 'x-amz-date':
                    amz_date = str(v)
                    break

        if not amz_date:
            logger.warning("Missing x-amz-date header")
            return False

        k_secret = ('AWS4' + secret_key).encode('utf-8')
        k_date = hmac.new(k_secret, date.encode('utf-8'), hashlib.sha256).digest()
        k_region = hmac.new(k_date, region.encode('utf-8'), hashlib.sha256).digest()
        k_service = hmac.new(k_region, service.encode('utf-8'), hashlib.sha256).digest()
        k_signing = hmac.new(k_service, b'aws4_request', hashlib.sha256).digest()

        for header_variant in _host_variants(normalized_headers):
            canonical_headers = []
            missing_signed_header = False
            for header_name in signed_header_names:
                header_value = header_variant.get(header_name)
                if header_value is None:
                    missing_signed_header = True
                    break
                canonical_headers.append(f"{header_name}:{' '.join(header_value.split())}")

            if missing_signed_header:
                continue

            canonical_headers_str = '\n'.join(canonical_headers) + '\n'
            canonical_request = '\n'.join([
                method,
                canonical_uri,
                canonical_query_string,
                canonical_headers_str,
                signed_headers_str,
                payload_hash,
            ])
            canonical_request_hash = hashlib.sha256(canonical_request.encode('utf-8')).hexdigest()
            string_to_sign = '\n'.join([
                algorithm,
                amz_date,
                credential_scope,
                canonical_request_hash,
            ])

            calculated_signature = hmac.new(
                k_signing, string_to_sign.encode('utf-8'), hashlib.sha256,
            ).hexdigest()

            if hmac.compare_digest(calculated_signature, provided_signature):
                return True

        logger.warning("Signature mismatch for presigned request")
        return False

    except Exception as e:
        logger.error(f"Error verifying signature: {e}", exc_info=True)
        return False
