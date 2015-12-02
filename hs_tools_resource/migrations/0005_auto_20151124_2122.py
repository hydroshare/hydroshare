# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hs_tools_resource', '0004_auto_20151112_1836'),
    ]

    operations = [
        migrations.AlterField(
            model_name='requesturlbase',
            name='value',
            field=models.CharField(default=b'NOT SPECIFIED', max_length=1024),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='toolversion',
            name='value',
            field=models.CharField(default=b'NOT SPECIFIED', max_length=128),
            preserve_default=True,
        ),
    ]
