# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations
from django.core.management import call_command


def forwards(apps, schema_editor):
    call_command('regenerate_xml_files_composite_resource', verbosity=3, interactive=False)

class Migration(migrations.Migration):

    dependencies = [
        ('hs_core', '0037_auto_20180209_0309'),
    ]

    operations = [
        migrations.RunPython(forwards)
    ]
