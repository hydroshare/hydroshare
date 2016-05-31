# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hs_core', '0021_auto_20160427_1807'),
    ]

    operations = [
        migrations.AddField(
            model_name='resourcefile',
            name='fed_resource_file_size',
            field=models.CharField(max_length=15, null=True, blank=True),
        ),
    ]
