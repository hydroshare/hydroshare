# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('theme', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='country',
            field=models.CharField(help_text=b'Country where you live.', max_length=1024, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='userprofile',
            name='middle_name',
            field=models.CharField(max_length=1024, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='userprofile',
            name='state',
            field=models.CharField(help_text=b'State/Province where you live.', max_length=1024, null=True, blank=True),
            preserve_default=True,
        ),
    ]
