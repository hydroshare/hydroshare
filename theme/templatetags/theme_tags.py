from __future__ import unicode_literals
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

