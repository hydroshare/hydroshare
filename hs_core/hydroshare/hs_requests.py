# -*- coding: utf-8 -*-

"""
This bypasses firewalls to allow nginx to be called from within HydroShare
via its docker container address. Otherwise, Nginx cannot be directly queries
from within a docker container because it is advertised in public as an address
on the other side of the firewall.
"""

import requests
import urlparse
from django.conf import settings


def get_nginx_ip():
    """
    Read the Nginx IP address from a local file, where it is stored during every restart.
    """
    ip = None
    with open("tmp/nginx_ip", "r") as fd:
        for line in fd:
            ip = line
            break
    return ip.strip()


def localize_url(url):
    """
    Localize an inward-pointing url so that it hits inside the HydroShare docker stack
    rather than an exterior firewall.  Do nothing if the uri is external.
    This also localizes references to www.hydroshare.org to the internal address,
    so that they work even during testing.
    """
    # TODO: handle non-standard ports with schemes http, https.
    parsed = urlparse.urlparse(url)
    # www.hydroshare.org or dev-machine-name.domain.org
    if parsed[1] == settings.PROD_FQDN_OR_IP or \
       parsed[1] == settings.FQDN_OR_IP:
        # insert local IP instead of fake target
        parsed2 = urlparse.ParseResult(parsed[0], get_nginx_ip(), parsed[2],
                                       parsed[3], parsed[4], parsed[5])
        return parsed2.geturl()
    else:
        return url


def get(url, *args, **kwargs):
    return requests.get(localize_url(url), *args, **kwargs)


def post(url, *args, **kwargs):
    return requests.post(localize_url(url), *args, **kwargs)
