# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hs_core', '0004_auto_20150721_1125'),
        ('hs_swat_modelinstance', '0002_auto_20150813_1726'),
    ]

    operations = [
        migrations.CreateModel(
            name='SWATModelInstanceResource',
            fields=[
            ],
            options={
                'ordering': ('_order',),
                'verbose_name': 'SWAT Model Instance Resource',
                'proxy': True,
            },
            bases=('hs_core.genericresource',),
        ),
    ]
