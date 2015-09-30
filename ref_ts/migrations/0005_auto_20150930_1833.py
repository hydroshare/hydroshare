# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hs_core', '0006_auto_20150917_1515'),
        ('ref_ts', '0004_auto_20150924_2249'),
    ]

    operations = [
        migrations.DeleteModel(
            name='RefTimeSeries',
        ),
        migrations.CreateModel(
            name='RefTimeSeriesResource',
            fields=[
            ],
            options={
                'ordering': ('_order',),
                'verbose_name': 'HIS Referenced Time Series',
                'proxy': True,
            },
            bases=('hs_core.baseresource',),
        ),
    ]
