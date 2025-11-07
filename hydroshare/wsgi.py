"""
WSGI config for HydroShare project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.8/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application
from django.contrib.staticfiles.handlers import StaticFilesHandler

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "hydroshare.settings")

application = get_wsgi_application()

if os.environ.get("DJANGO_DEBUG", "true").lower() == "true":
    application = StaticFilesHandler(application)
