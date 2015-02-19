# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('theme', '0002_auto_20150105_0223'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='details',
            field=models.TextField(help_text=b'Tell the HydroShare community a little about yourself.', null=True, verbose_name=b'Description', blank=True),
            preserve_default=True,
        ),
    ]
