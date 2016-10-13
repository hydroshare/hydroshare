# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hs_tracking', '0003_auto_20160623_1718'),
    ]

    operations = [
        migrations.AlterField(
            model_name='variable',
            name='value',
            field=models.CharField(max_length=500),
        ),
    ]
