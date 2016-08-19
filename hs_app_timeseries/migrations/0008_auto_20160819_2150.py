# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hs_app_timeseries', '0007_timeseriesresult_series_label'),
    ]

    operations = [
        migrations.AddField(
            model_name='site',
            name='latitude',
            field=models.FloatField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='site',
            name='longitude',
            field=models.FloatField(null=True, blank=True),
        ),
    ]
