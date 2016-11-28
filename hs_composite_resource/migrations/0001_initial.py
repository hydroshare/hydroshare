# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hs_core', '0029_auto_20161128_1820'),
    ]

    operations = [
        migrations.CreateModel(
            name='CompositeResource',
            fields=[
            ],
            options={
                'ordering': ('_order',),
                'verbose_name': 'Composite',
                'proxy': True,
            },
            bases=('hs_core.baseresource',),
        ),
    ]
