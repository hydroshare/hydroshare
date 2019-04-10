# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hs_tools_resource', '0010_auto_20161203_1913'),
    ]

    operations = [
        migrations.AddField(
            model_name='toolicon',
            name='data_url',
            field=models.TextField(default=b'', blank=True),
        ),
    ]
