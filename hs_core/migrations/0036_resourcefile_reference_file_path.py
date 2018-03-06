# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hs_core', '0035_remove_deprecated_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='resourcefile',
            name='reference_file_path',
            field=models.CharField(max_length=255, null=True, blank=True),
        ),
    ]
