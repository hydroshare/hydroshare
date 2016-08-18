# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hs_app_timeseries', '0006_timeseriesmetadata_series_names'),
    ]

    operations = [
        migrations.AddField(
            model_name='timeseriesresult',
            name='series_label',
            field=models.CharField(max_length=255, null=True, blank=True),
        ),
    ]
