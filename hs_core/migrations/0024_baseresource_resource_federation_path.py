# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hs_core', '0023_merge'),
    ]

    operations = [
        migrations.AddField(
            model_name='baseresource',
            name='resource_federation_path',
            field=models.CharField(default=b'', max_length=100, blank=True),
        ),
    ]
