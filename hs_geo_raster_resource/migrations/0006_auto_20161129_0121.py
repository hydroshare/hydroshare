# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hs_geo_raster_resource', 'custom_migration_for_raster_meta_update_20160512'),
    ]

    operations = [
        migrations.AlterField(
            model_name='originalcoverage',
            name='_value',
            field=models.CharField(max_length=10000, null=True),
        ),
    ]
