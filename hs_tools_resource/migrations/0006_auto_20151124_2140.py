# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hs_tools_resource', '0005_auto_20151124_2122'),
    ]

    operations = [
        migrations.AlterField(
            model_name='requesturlbase',
            name='value',
            field=models.CharField(max_length=1024, null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='toolversion',
            name='value',
            field=models.CharField(max_length=128),
            preserve_default=True,
        ),
    ]
