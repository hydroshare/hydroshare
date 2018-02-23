# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hs_core', '0036_resourcefile_reference_file_path'),
    ]

    operations = [
        migrations.AddField(
            model_name='resourcefile',
            name='reference_file_size',
            field=models.CharField(max_length=15, null=True, blank=True),
        ),
    ]
