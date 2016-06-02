# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hs_app_timeseries', '0004_auto_20160526_2026'),
    ]

    operations = [
        migrations.AddField(
            model_name='method',
            name='series_id',
            field=models.CharField(max_length=36, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='processinglevel',
            name='series_id',
            field=models.CharField(max_length=36, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='site',
            name='series_id',
            field=models.CharField(max_length=36, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='timeseriesresult',
            name='series_id',
            field=models.CharField(max_length=36, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='variable',
            name='series_id',
            field=models.CharField(max_length=36, null=True, blank=True),
        ),
        migrations.AlterUniqueTogether(
            name='method',
            unique_together=set([('content_type', 'object_id', 'series_id')]),
        ),
        migrations.AlterUniqueTogether(
            name='processinglevel',
            unique_together=set([('content_type', 'object_id', 'series_id')]),
        ),
        migrations.AlterUniqueTogether(
            name='site',
            unique_together=set([('content_type', 'object_id', 'series_id')]),
        ),
        migrations.AlterUniqueTogether(
            name='timeseriesresult',
            unique_together=set([('content_type', 'object_id', 'series_id')]),
        ),
        migrations.AlterUniqueTogether(
            name='variable',
            unique_together=set([('content_type', 'object_id', 'series_id')]),
        ),
    ]
