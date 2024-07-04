# -*- coding: utf-8 -*-

"""
This bypasses firewalls to allow Nginx to be called from within HydroShare
via its docker container address. Otherwise, HS cannot be reliably queried
from within a docker container because it is advertised in DNS as an address
on the other side of any firewall.

This is mainly used in end-to-end testing implemented in management commands.
"""

import requests
import urllib.parse
from django.conf import settings


def get_local_ip():
    """
    Read the Nginx IP address from a local file, where it is stored during
    every nginx restart. This address is dynamic and changes on every restart.
    """
    return '127.0.0.1'


def localize_url(url):
    """
    Localize an inward-pointing url so that it hits inside the HydroShare
    docker stack rather than an exterior firewall.  Do nothing if the uri
    is external.  This also localizes references to www.hydroshare.org
    to the internal address, so that urls embedded in metadata can be
    accessed from a docker container for loopback testing.
    """
    parsed = urllib.parse.urlparse(url)
    # www.hydroshare.org or dev-machine-name.domain.org
    if parsed[1] == getattr(settings, 'PROD_FQDN_OR_IP', 'www.hydroshare.org') or \
       parsed[1] == getattr(settings, 'FQDN_OR_IP', 'www.hydroshare.org'):
        # insert local IP instead of fake target
        parsed2 = urllib.parse.ParseResult(parsed[0], get_local_ip(), parsed[2],
                                           parsed[3], parsed[4], parsed[5])
        return parsed2.geturl()
    else:
        return url


def get(url, *args, **kwargs):
    """ call requests.get on a localized url """
    return requests.get(localize_url(url), *args, **kwargs)


def post(url, *args, **kwargs):
    """ call requests.post on a localized url """
    return requests.post(localize_url(url), *args, **kwargs)
