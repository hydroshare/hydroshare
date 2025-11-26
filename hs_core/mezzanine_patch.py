from django.contrib.sites.models import Site

# Shared cache for single-site application
_CACHED_SITE = None
_CACHED_SITE_BY_DOMAIN = {}


def _get_cached_site():
    """Get or initialize the cached site instance by pk."""
    global _CACHED_SITE
    if _CACHED_SITE is None:
        from mezzanine.utils.sites import current_site_id
        _CACHED_SITE = Site.objects.get_original(pk=current_site_id())
    return _CACHED_SITE


def patched_site_get_current():
    """
    Patch for Site.objects.get_current() that returns a cached instance.
    Single-site application only needs one Site object.
    """
    return _get_cached_site()


def _cached_get_by_domain(domain):
    """Cache domain lookups (single-site application)."""
    cache_key = domain
    if cache_key in _CACHED_SITE_BY_DOMAIN:
        # Cache hit - return cached instance
        return _CACHED_SITE_BY_DOMAIN[cache_key]

    # Cache miss - query database and cache result
    try:
        result = Site.objects.get_original(domain__iexact=domain)
        _CACHED_SITE_BY_DOMAIN[cache_key] = result
        return result
    except Site.DoesNotExist:
        # Site doesn't exist yet (e.g., during early startup or tests)
        # Create it on-the-fly for 'testserver' domain
        if domain.lower() == 'testserver':
            result = Site.objects.create(domain=domain, name=domain)
            _CACHED_SITE_BY_DOMAIN[cache_key] = result
            return result
        raise


def patched_site_get(**kwargs):
    """
    Patch for Site.objects.get that caches common lookups.
    For single-site applications, returns cached instance when possible.
    """
    # Cache domain__iexact lookups
    if "domain__iexact" in kwargs:
        domain = kwargs["domain__iexact"]
        return _cached_get_by_domain(domain)

    # Cache pk lookups for the current site
    if "pk" in kwargs:
        from mezzanine.utils.sites import current_site_id
        if kwargs["pk"] == current_site_id():
            return _get_cached_site()

    # Fallback to original behavior for other lookups
    return Site.objects.get_original(**kwargs)
