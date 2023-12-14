
from django.conf import settings
from mezzanine import template
from mezzanine.utils.sites import current_site_id
from theme.models import SiteConfiguration

register = template.Library()


@register.as_tag
def get_site_conf():
    """
    Adds the `SiteConfiguration` to the context
    """
    return SiteConfiguration.objects.get_or_create(site_id=current_site_id())[0]


@register.as_tag
def get_recaptcha_site_key():
    return settings.RECAPTCHA_SITE_KEY
