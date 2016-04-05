from __future__ import absolute_import

# Import defusedexpat here so that it can patch the standard library's expat XML parser, which is used by
# rdflib and other libraries in other parts of the app.
try:
    import defusedexpat
    # Import logging after defusedexpat in case logging uses XML (who knows)
    import logging
    logger = logging.getLogger(__name__)
    logger.warning("Using defusedexpat.  GOOD!")
except ImportError:
    import logging
    logger = logging.getLogger(__name__)
    msg = ("Unable to import defusedexpat. "
           "Not using defusedexpat is only acceptable in testing environments. "
           "In production not using defusedexpat could result in security vulnerabilities. "
           "For more information see: https://docs.python.org/2.7/library/xml.html#xml-vulnerabilities")
    logger.critical(msg)

from .celery import app as celery_app
