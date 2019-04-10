# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('theme', '0002_auto_20160219_2039'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='userprofile',
            name='organization_type',
        ),
        migrations.RemoveField(
            model_name='userprofile',
            name='profession',
        ),
        migrations.AddField(
            model_name='userprofile',
            name='country',
            field=models.CharField(max_length=1024, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='middle_name',
            field=models.CharField(max_length=1024, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='state',
            field=models.CharField(max_length=1024, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='user_type',
            field=models.CharField(default=b'Unspecified', max_length=1024, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='website',
            field=models.URLField(null=True, blank=True),
        ),
    ]
