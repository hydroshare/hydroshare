# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ref_ts', '0002_auto_20150122_2205'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='reftimeseries',
            name='data_site_code',
        ),
        migrations.RemoveField(
            model_name='reftimeseries',
            name='data_site_name',
        ),
        migrations.RemoveField(
            model_name='reftimeseries',
            name='end_date',
        ),
        migrations.RemoveField(
            model_name='reftimeseries',
            name='variable_code',
        ),
        migrations.RemoveField(
            model_name='reftimeseries',
            name='variable_name',
        ),
    ]
