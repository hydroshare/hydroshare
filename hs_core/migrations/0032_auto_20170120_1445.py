# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hs_core', '0031_auto_20170112_2202'),
    ]

    operations = [
        migrations.AlterField(
            model_name='resourcefile',
            name='file_folder',
            field=models.CharField(max_length=4096, null=True, blank=True),
        ),
    ]
