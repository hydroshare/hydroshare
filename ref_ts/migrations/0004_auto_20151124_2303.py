# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hs_access_control', '0004_remove_useraccess_admin'),
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
        migrations.RemoveField(
            model_name='method',
            name='value',
        ),
        migrations.RemoveField(
            model_name='qualitycontrollevel',
            name='value',
        ),
        migrations.AddField(
            model_name='method',
            name='code',
            field=models.CharField(default=b'', max_length=200),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='method',
            name='description',
            field=models.CharField(default=b'', max_length=200),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='qualitycontrollevel',
            name='code',
            field=models.CharField(default=b'', max_length=200),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='qualitycontrollevel',
            name='definition',
            field=models.CharField(default=b'', max_length=200),
            preserve_default=True,
        ),
    ]
