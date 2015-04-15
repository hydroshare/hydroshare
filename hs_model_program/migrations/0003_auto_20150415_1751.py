# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('hs_model_program', '0002_auto_20150313_1656'),
    ]

    operations = [
        migrations.AlterField(
            model_name='mpmetadata',
            name='date_released',
            field=models.DateTimeField(default=datetime.datetime(2015, 4, 15, 17, 51, 47, 91816), help_text=b'The date of the software release (m/d/Y H:M)', null=True, verbose_name=b'Release Date', blank=True),
            preserve_default=True,
        ),
    ]
