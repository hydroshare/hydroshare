""" This module contains miscellaneous utility functions and classes for creating the OWS webservices.  The most useful
functions in the module are probably the date manipulation functions.
"""

from collections import namedtuple
import datetime
from django.core.exceptions import ValidationError
from django.forms import MultipleChoiceField, Field
from django.utils.formats import sanitize_separators
from osgeo import osr
import re

def _from_today(match):    
    plusminus = match.group(1)
    amt = match.group(2)

    if plusminus == '-':
        return datetime.date.today() - datetime.timedelta(days=int(amt))
    else:
        return datetime.date.today() + datetime.timedelta(days=int(amt))

def _from_now(match):
    def maybeint(i):
        if i:
            return int(i)
        else:
            return 0

    plusminus = match.group(1)
    weeks = maybeint( match.group(2) )
    days = maybeint( match.group(3) )
    hours =  maybeint(match.group(4) )
    mins =maybeint(match.group(5) )
    seconds = maybeint(match.group(6))
    milliseconds = maybeint(match.group(7))


    if plusminus == '-':
        return datetime.datetime.utcnow() - datetime.timedelta(
            weeks=weeks, days=days, hours=hours, mins=mins, seconds=seconds, milliseconds=milliseconds)

def parsetime(t):
    """Parses a time string into a datetime object.  This is the function used by parse the dates in an OWS request, so
    all OWS requests accept these date formats.  ParseTime accepts the following formats:
        
        * '%Y.%m.%d-%H:%M:%S.%f'
        * '%Y.%m.%d-%H:%M:%S'
        * '%Y.%m.%d-%H:%M'
        * '%Y.%m.%d'
        * '%Y%m%d%H%M%S%f'
        * '%Y%m%d%H%M%S'
        * '%Y%m%d%H%M'
        * '%Y%m%d'
        * '%Y.%m'
        * '%Y'
        * '%Y.%m.%d-%H:%M:%S.%f'
        * '%Y/%m/%d-%H:%M:%S'
        * '%Y/%m/%d-%H:%M'
        * '%Y/%m/%d'
        * '%Y/%m'
        * '%Y'
        * "now"
        * "today"
        * "today+${days}"
        * "now+${weeks}w${days}d${hours}h${mins}m${seconds}s${millisecs}ms"
    
    :param t: a string in one of the above formats.
    :return: a datetime object
    """
    
    timeformats = [
        '%Y.%m.%d-%H:%M:%S.%f',
        '%Y.%m.%d-%H:%M:%S',
        '%Y.%m.%d-%H:%M',
        '%Y.%m.%d',
        '%Y%m%d%H%M%S%f',
        '%Y%m%d%H%M%S',
        '%Y%m%d%H%M',
        '%Y%m%d',
        '%Y.%m',
        '%Y',
        '%Y.%m.%d-%H:%M:%S.%f',
        '%Y/%m/%d-%H:%M:%S',
        '%Y/%m/%d-%H:%M',
        '%Y/%m/%d',
        '%Y/%m',
        '%Y'
    ]
    alt_formats = {
       'now' : datetime.datetime.utcnow(),
       'today' : datetime.date.today(),
    }
    high_level = [
        (re.compile('today(\+|-)([0-9]+)'), _from_today),
        (re.compile('now(\+|-)([0-9]+w)?([0-9]+d)?([0-9]+h)?([0-9]+m)?([0-9]+s)?([0-9]+ms)?'), _from_now)
    ]

    if not t:
        return None

    ret = None
    for tf in timeformats:
        try:
            ret = datetime.datetime.strptime(t, tf)
        except:
            pass

    if not ret and t in alt_formats:
        return alt_formats[t]
    elif not ret:
        for tf, l in high_level:
            k = tf.match(t)
            if k:
                ret = l(k)
    if ret:
        return ret
    else:
        raise ValueError('time data does not match any valid format: ' + t)

def create_spatialref(srs, srs_format='srid'):
    """
    **Deprecated - use Django's SpatialRef class**. Create an :py:class:`osgeo.osr.SpatialReference` from an srid, wkt,
    projection, or epsg code.  srs_format should be one of: srid, wkt, proj,
    epsg to represent a format in numerical srid form, well-known text, proj4,
    or epsg formats.
    """
    spatialref = osr.SpatialReference()
    if srs_format:
        if srs_format == 'srid':
            spatialref.ImportFromEPSG(srs)
        elif srs_format == 'wkt':
            spatialref.ImportFromWkt(srs)
        elif srs_format == 'proj':
            spatialref.ImportFromProj4(srs)
    else:
        spatialref.ImportFromEPSG(int(srs.split(':')[1]))
    return spatialref

mimetypes = namedtuple("MimeTypes", (
    'json', 'jsonp')
)(
    json='application/json',
    jsonp='text/plain'
)


class CaseInsensitiveDict(dict):
    """
    A subclass of :py:class:django.utils.datastructures.MultiValueDict that treats all keys as lower-case strings
    """

    def __init__(self, key_to_list_mapping=()):
        def fix(pair):
            key, value = pair
            return key.lower(),value
        super(CaseInsensitiveDict, self).__init__([fix(kv) for kv in key_to_list_mapping])

    def __getitem__(self, key):
        return super(CaseInsensitiveDict, self).__getitem__(key.lower())

    def __setitem__(self, key, value):
        return super(CaseInsensitiveDict, self).__setitem__(key.lower(), value)

    def get(self, key, default=None):
        if key not in self:
            return default
        else:
            return self[key]

    def getlist(self, key):
        if key not in self:
            return []
        elif isinstance(self[key], list):
            return self[key]
        elif isinstance(self[key], tuple):
            return list(self[key])
        else:
            return [self[key]]


class MultipleValueField(MultipleChoiceField):
    """A field for pulling in arbitrary lists of strings instead of constraining them by choice"""
    def validate(self, value):
        if self.required and not value:
            raise ValidationError(self.error_messages['required'])

class BBoxField(Field):
    """A field that represents a bounding box in minx,miny,maxx,maxy format - parses the bbox field from an OWS request.
    """
    def to_python(self, value):
        value = super(BBoxField, self).to_python(value)
        if not value:
            return -180.0,-90.0,180.0,90.0

        try:
            lx, ly, ux, uy = value.split(',')
            if self.localize:
                lx = float(sanitize_separators(lx))
                ly = float(sanitize_separators(ly))
                ux = float(sanitize_separators(ux))
                uy = float(sanitize_separators(uy))

                if uy < ly or ux < lx:
                    raise ValidationError("BBoxes must be in lower-left(x,y), upper-right(x,y) order")
        except (ValueError, TypeError):
            raise ValidationError("BBoxes must be four floating point values separated by commas")

        lx = float(sanitize_separators(lx))
        ly = float(sanitize_separators(ly))
        ux = float(sanitize_separators(ux))
        uy = float(sanitize_separators(uy))
        return lx, ly, ux, uy
