# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hs_app_netCDF', '0005_auto_20161111_2322'),
    ]

    operations = [
        migrations.AlterField(
            model_name='originalcoverage',
            name='projection_string_type',
            field=models.CharField(max_length=20, null=True, choices=[(b'', b'---------'), (b'WKT String', b'WKT String'), (b'Proj4 String', b'Proj4 String')]),
        ),
    ]
