# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hs_geo_raster_resource', '0003_auto_20150313_2136'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bandinformation',
            name='name',
            field=models.CharField(max_length=500, null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='cellinformation',
            name='name',
            field=models.CharField(max_length=500, null=True),
            preserve_default=True,
        ),
    ]
