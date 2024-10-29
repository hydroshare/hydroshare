#!/usr/bin/env python
import os
import sys

from django.core.management import execute_from_command_line
from opentelemetry.instrumentation.django import DjangoInstrumentor

# TODO: still need to configure the trace exporter:
# opentelemetry-exporter-gcp-trace

if __name__ == "__main__":
    os.environ.setdefault("PYTHONPATH", '/hydroshare')
    os.environ.setdefault("TMPDIR", "/tmp")
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "hydroshare.settings")
    DjangoInstrumentor().instrument()

    execute_from_command_line(sys.argv)
