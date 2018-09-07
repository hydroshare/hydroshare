# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from hs_core.models import Identifier

from django.db import migrations


def remove_dx(apps, schema_editor):
    for id in Identifier.objects.filter(url__startswith='http://dx.'):
        id.url = id.url.replace('http://dx.', 'https://')
        id.save()

def backwards(apps, schema_editor):
    # adding backwards for testing
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('hs_core', '0037_auto_20180209_0309'),
    ]

    operations = [
        migrations.RunPython(remove_dx, backwards),
    ]
