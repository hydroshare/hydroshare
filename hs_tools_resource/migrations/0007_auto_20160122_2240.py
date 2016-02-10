# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hs_tools_resource', '0006_auto_20160113_2003'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='toolicon',
            name='icon',
        ),
        migrations.AddField(
            model_name='toolicon',
            name='url',
            field=models.CharField(max_length=1024, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='toolversion',
            name='value',
            field=models.CharField(max_length=128, blank=True),
            preserve_default=True,
        ),
    ]
