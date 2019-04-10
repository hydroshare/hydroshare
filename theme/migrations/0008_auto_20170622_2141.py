# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('theme', '0007_auto_20170427_1553'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userquota',
            name='allocated_value',
            field=models.FloatField(default=20),
        ),
        migrations.AlterField(
            model_name='userquota',
            name='used_value',
            field=models.FloatField(default=0),
        ),
    ]
