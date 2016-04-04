from __future__ import absolute_import

# Import defusedexpat here so that it can patch the standard library's expat XML parser, which is used by
# rdflib and other libraries in other parts of the app.
import defusedexpat

from .celery import app as celery_app
