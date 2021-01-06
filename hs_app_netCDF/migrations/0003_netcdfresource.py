# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hs_core', '0004_auto_20150721_1125'),
        ('hs_app_netCDF', '0002_auto_20150813_1215'),
    ]

    operations = [
        migrations.CreateModel(
            name='NetcdfResource',
            fields=[
            ],
            options={
                'ordering': ('_order',),
                'verbose_name': 'Multidimensional (NetCDF)',
                'proxy': True,
            },
            bases=('hs_core.genericresource',),
        ),
    ]
