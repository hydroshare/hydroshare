import hmac

from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET

from .settings import get_resource_s3_zones_config


@require_GET
@never_cache
def zone_configuration(request):
    if not getattr(settings, "S3_ZONES_DATABASE_ENABLED", False):
        return HttpResponse(status=404)
    token_file = settings.S3_ZONE_API_TOKEN_FILE
    if not token_file:
        raise ValueError("S3_ZONE_API_TOKEN_FILE is required for database zones")
    with open(token_file, encoding="utf-8") as file:
        token = file.read().strip()
    if not token:
        raise ValueError("S3 zone API token must not be empty")
    supplied = request.headers.get("Authorization", "")
    if not hmac.compare_digest(supplied.encode("utf-8"), f"Bearer {token}".encode("utf-8")):
        return HttpResponse(status=403)
    zones = get_resource_s3_zones_config().resource_s3_zones_config
    return JsonResponse({name: zone.model_dump() for name, zone in zones.items()})
