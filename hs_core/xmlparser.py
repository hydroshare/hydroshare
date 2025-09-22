"""Extend ExpatParser with hydroshare-specific functionality."""

import base64
import os.path
from io import StringIO
from xml.sax import xmlreader, saxutils
# TODO: should we use defusedxml.sax?
from xml.sax.expatreader import ExpatParser

from django.conf import settings


XML_CACHE = os.path.join(settings.PROJECT_ROOT, '_xmlcache')


class CatalogedExpatParser(ExpatParser):
    """Extend ExpatParser with cataloging capabilities."""

    def external_entity_ref(self, context, base, sysid, pubid):
        """Add external entity reference to XML document."""
        if not self._external_ges:
            return 1

        source = self._ent_handler.resolveEntity(pubid, sysid)
        source = saxutils.prepare_input_source(source,
                                               self._source.getSystemId()
                                               or "")

        # If an entry does not exist in the xml cache, create it.
        filepath = os.path.join(XML_CACHE, base64.urlsafe_b64encode(pubid))
        if not os.path.isfile(filepath):
            with open(filepath, 'w') as f:
                contents = source.getByteStream().read()
                source.setByteStream(StringIO(contents))
                f.write(contents)

        self._entity_stack.append((self._parser, self._source))
        self._parser = self._parser.ExternalEntityParserCreate(context)
        self._source = source

        try:
            xmlreader.IncrementalParser.parse(self, source)
        except:  # noqa
            return 0  # FIXME: save error info here?

        (self._parser, self._source) = self._entity_stack[-1]
        del self._entity_stack[-1]
        return 1


class CatalogEntityResolver(object):
    """Respove catalog entities based on file path."""

    def resolveEntity(self, publicId, systemId):
        """Respove catalog entities based on file path."""
        filepath = os.path.join(XML_CACHE, base64.urlsafe_b64encode(publicId))
        if os.path.isfile(filepath):
            source = xmlreader.InputSource()
            with open(filepath, 'r') as f:
                source.setByteStream(StringIO(f.read()))
            return source

        return systemId


def create_parser(*args, **kwargs):
    """Create extended XML parser."""
    parser = CatalogedExpatParser(*args, **kwargs)
    parser.setEntityResolver(CatalogEntityResolver())

    return parser
