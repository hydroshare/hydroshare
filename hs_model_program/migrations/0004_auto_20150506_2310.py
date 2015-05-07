# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('hs_model_program', '0003_auto_20150415_1751'),
    ]

    operations = [
        migrations.AlterField(
            model_name='modelprogramresource',
            name='owners',
            field=models.ManyToManyField(help_text=b'The person who has total ownership of the resource', related_name='owns_hs_model_program_modelprogramresource', to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='mpmetadata',
            name='date_released',
            field=models.DateTimeField(default=datetime.datetime(2015, 5, 6, 23, 10, 23, 958753), help_text=b'The date of the software release (m/d/Y H:M)', null=True, verbose_name=b'Release Date', blank=True),
            preserve_default=True,
        ),
    ]
