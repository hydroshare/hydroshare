# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations
from django.core.management import call_command


def forwards(apps, schema_editor):
    call_command('remove_auto_generated_generic_metadata', verbosity=3, interactive=False)

class Migration(migrations.Migration):

    dependencies = [
        ('hs_core', '0038_regenerate_xml_files_composite_resource'),
    ]

    operations = [
        migrations.RunPython(forwards)
    ]
