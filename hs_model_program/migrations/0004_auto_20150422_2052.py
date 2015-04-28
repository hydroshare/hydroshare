# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('hs_model_program', '0003_auto_20150415_1751'),
    ]

    operations = [
        migrations.AlterField(
            model_name='mpmetadata',
            name='date_released',
            field=models.DateTimeField(default=datetime.datetime(2015, 4, 22, 20, 52, 4, 217285), help_text=b'The date of the software release (m/d/Y H:M)', null=True, verbose_name=b'Release Date', blank=True),
            preserve_default=True,
        ),
    ]
