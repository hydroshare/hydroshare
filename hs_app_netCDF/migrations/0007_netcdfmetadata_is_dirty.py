# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hs_app_netCDF', '0006_auto_20170120_1445'),
    ]

    operations = [
        migrations.AddField(
            model_name='netcdfmetadata',
            name='is_dirty',
            field=models.BooleanField(default=False),
        ),
    ]
