# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hs_core', '0034_manual_migrate_file_paths'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='resourcefile',
            name='fed_resource_file_name_or_path',
        ),
        migrations.RemoveField(
            model_name='resourcefile',
            name='fed_resource_file_size',
        ),
    ]
