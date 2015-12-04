# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hs_geo_raster_resource', '0003_auto_20150813_1315'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cellinformation',
            name='noDataValue',
            field=models.FloatField(null=True, blank=True),
            preserve_default=True,
        ),
    ]
