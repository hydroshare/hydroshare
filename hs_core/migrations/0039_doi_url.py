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
        ('hs_core', '0038_auto_20180831_2201'),
    ]

    operations = [
        migrations.RunPython(remove_dx, backwards),
    ]
