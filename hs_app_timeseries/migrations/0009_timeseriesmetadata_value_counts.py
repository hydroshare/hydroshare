# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.contrib.postgres.fields.hstore


class Migration(migrations.Migration):

    dependencies = [
        ('hs_app_timeseries', '0008_auto_20160819_2150'),
    ]

    operations = [
        migrations.AddField(
            model_name='timeseriesmetadata',
            name='value_counts',
            field=django.contrib.postgres.fields.hstore.HStoreField(default={}),
        ),
    ]
