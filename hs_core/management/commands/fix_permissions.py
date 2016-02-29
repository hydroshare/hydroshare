# -*- coding: utf-8 -*-

"""Add permissions for proxy model.
This is needed because of the bug https://code.djangoproject.com/ticket/11154
in Django (as of 1.6, it's not fixed).
When a permission is created for a proxy model, it actually creates if for it's
base model app_label (eg: for "article" instead of "about", for the About proxy
model).
What we need, however, is that the permission be created for the proxy model
itself, in order to have the proper entries displayed in the admin.
"""

from __future__ import unicode_literals, absolute_import, division

import sys

from django.contrib.auth.management import _get_all_permissions
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand
from django.apps import apps
from django.utils.encoding import smart_unicode


class Command(BaseCommand):
    help = "Fix permissions for proxy models."

    def handle(self, *args, **options):
        for model in apps.get_models():
            opts = model._meta
            ctype, created = ContentType.objects.get_or_create(
                app_label=opts.app_label,
                model=opts.object_name.lower(),
                defaults={'name': smart_unicode(opts.verbose_name_raw)})

            for codename, name in _get_all_permissions(opts, ctype):
                p, created = Permission.objects.get_or_create(
                    codename=codename,
                    content_type=ctype,
                    defaults={'name': name})
                if created:
                    sys.stdout.write('Adding permission {}\n'.format(p))
