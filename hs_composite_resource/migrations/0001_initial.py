# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hs_core', '0031_auto_20161220_2323'),
    ]

    operations = [
        migrations.CreateModel(
            name='CompositeResource',
            fields=[
            ],
            options={
                'ordering': ('_order',),
                'verbose_name': 'Composite Resource',
                'proxy': True,
            },
            bases=('hs_core.baseresource',),
        ),
    ]
