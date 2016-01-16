# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hs_swat_modelinstance', '0005_auto_20151110_1945'),
    ]

    operations = [
        migrations.AlterField(
            model_name='modelinput',
            name='watershedArea',
            field=models.CharField(max_length=100, null=True, verbose_name=b'Watershed area in square kilometers', blank=True),
            preserve_default=True,
        ),
    ]
