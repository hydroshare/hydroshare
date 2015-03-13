# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('hs_model_program', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='modelprogramresource',
            name='rating_average',
            field=models.FloatField(default=0, editable=False),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='modelprogramresource',
            name='rating_count',
            field=models.IntegerField(default=0, editable=False),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='modelprogramresource',
            name='rating_sum',
            field=models.IntegerField(default=0, editable=False),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='mpmetadata',
            name='date_released',
            field=models.DateTimeField(default=datetime.datetime(2015, 3, 13, 16, 56, 42, 763326), help_text=b'The date of the software release (m/d/Y H:M)', null=True, verbose_name=b'Release Date', blank=True),
            preserve_default=True,
        ),
    ]
