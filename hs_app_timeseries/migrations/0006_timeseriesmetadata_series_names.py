# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.contrib.postgres.fields


class Migration(migrations.Migration):

    dependencies = [
        ('hs_app_timeseries', 'custom_data_migration_20160718'),
    ]

    operations = [
        migrations.AddField(
            model_name='timeseriesmetadata',
            name='series_names',
            field=django.contrib.postgres.fields.ArrayField(default=[], base_field=models.CharField(max_length=200, null=True, blank=True), size=None),
        ),
    ]
