# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hs_access_control', '0003_auto_20150824_2215'),
        ('hs_core', '0006_auto_20150917_1515'),
        ('ref_ts', '0003_reftimeseries'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='reftimeseries',
            name='baseresource_ptr',
        ),
        migrations.DeleteModel(
            name='RefTimeSeries',
        ),
        migrations.CreateModel(
            name='RefTimeSeries',
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
