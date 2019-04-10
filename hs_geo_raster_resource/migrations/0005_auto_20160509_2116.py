# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hs_geo_raster_resource', 'custom_migration_for_tif_to_vrt_20160223'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='cellinformation',
            name='noDataValue',
        ),
        migrations.AddField(
            model_name='bandinformation',
            name='maximumValue',
            field=models.TextField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='bandinformation',
            name='minimumValue',
            field=models.TextField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='bandinformation',
            name='noDataValue',
            field=models.TextField(null=True, blank=True),
        ),
    ]
