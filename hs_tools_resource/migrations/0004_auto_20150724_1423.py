# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from hs_tools_resource.models import ToolResource, OldToolResource


def migrate_to_baseresource(apps, schema_editor):
    # BaseResource = apps.get_model('hs_core', 'BaseResource')
    # OldToolResource = apps.get_model('hs_tools_resource', 'OldToolResource')

    for res in OldToolResource.objects.all():
        res.copy_to_new_model()

def migrate_from_baseresource(apps, schema_editor):
    #BaseResource = apps.get_model('hs_core', 'BaseResource')
    #OldToolResource = apps.get_model('hs_tools_resource', 'OldToolResource')
    pass

class Migration(migrations.Migration):

    dependencies = [
        ('hs_tools_resource', '0003_auto_20150724_1501'),
        ('hs_core', '0004_auto_20150721_1125'),
    ]

    operations = [
        migrations.RunPython(migrate_to_baseresource, migrate_from_baseresource),
    ]
