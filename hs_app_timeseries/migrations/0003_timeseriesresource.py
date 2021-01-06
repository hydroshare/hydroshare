# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hs_core', '0004_auto_20150721_1125'),
        ('hs_app_timeseries', '0002_auto_20150813_1247'),
    ]

    operations = [
        migrations.CreateModel(
            name='TimeSeriesResource',
            fields=[
            ],
            options={
                'ordering': ('_order',),
                'verbose_name': 'Time Series',
                'proxy': True,
            },
            bases=('hs_core.genericresource',),
        ),
    ]
