# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hs_core', '0030_auto_20161212_2205'),
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
