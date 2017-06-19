# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hs_app_timeseries', '0001_auto_20160829_2156'),
    ]

    operations = [
        migrations.AlterField(
            model_name='site',
            name='elevation_m',
            field=models.FloatField(null=True, blank=True),
        ),
    ]
