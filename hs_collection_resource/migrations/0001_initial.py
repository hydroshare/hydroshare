# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hs_core', '0020_baseresource_collections'),
    ]

    operations = [
        migrations.CreateModel(
            name='CollectionResource',
            fields=[
            ],
            options={
                'ordering': ('_order',),
                'verbose_name': 'Collection Resource',
                'proxy': True,
            },
            bases=('hs_core.baseresource',),
        ),
    ]
