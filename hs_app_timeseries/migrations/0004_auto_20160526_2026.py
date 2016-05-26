# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hs_app_timeseries', '0003_timeseriesresource'),
    ]

    operations = [
        migrations.AlterField(
            model_name='method',
            name='method_code',
            field=models.CharField(max_length=100),
        ),
    ]
