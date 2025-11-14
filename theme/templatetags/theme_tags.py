
from django.conf import settings
from django.core.cache import cache
from mezzanine import template
from mezzanine.utils.sites import current_site_id
from theme.models import SiteConfiguration

register = template.Library()


@register.as_tag
def get_site_conf():
    """
    Adds the `SiteConfiguration` to the context
    """
    site_id = current_site_id()
    cache_key = f"site_conf_{site_id}"
    site_conf = cache.get(cache_key)
    if not site_conf:
        site_conf, _ = SiteConfiguration.objects.get_or_create(site_id=site_id)
        cache.set(cache_key, site_conf, timeout = 60*60*24)  # cache for 1 day
    return site_conf


@register.as_tag
def get_recaptcha_site_key():
    return settings.RECAPTCHA_SITE_KEY
