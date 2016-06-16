# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.contrib.postgres.fields


class Migration(migrations.Migration):

    dependencies = [
        ('hs_app_timeseries', '0004_auto_20160526_2026'),
    ]

    operations = [
        migrations.AddField(
            model_name='method',
            name='is_dirty',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='method',
            name='series_ids',
            field=django.contrib.postgres.fields.ArrayField(default=[], base_field=models.CharField(max_length=36, null=True, blank=True), size=None),
        ),
        migrations.AddField(
            model_name='processinglevel',
            name='is_dirty',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='processinglevel',
            name='series_ids',
            field=django.contrib.postgres.fields.ArrayField(default=[], base_field=models.CharField(max_length=36, null=True, blank=True), size=None),
        ),
        migrations.AddField(
            model_name='site',
            name='is_dirty',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='site',
            name='series_ids',
            field=django.contrib.postgres.fields.ArrayField(default=[], base_field=models.CharField(max_length=36, null=True, blank=True), size=None),
        ),
        migrations.AddField(
            model_name='timeseriesresult',
            name='is_dirty',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='timeseriesresult',
            name='series_ids',
            field=django.contrib.postgres.fields.ArrayField(default=[], base_field=models.CharField(max_length=36, null=True, blank=True), size=None),
        ),
        migrations.AddField(
            model_name='variable',
            name='is_dirty',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='variable',
            name='series_ids',
            field=django.contrib.postgres.fields.ArrayField(default=[], base_field=models.CharField(max_length=36, null=True, blank=True), size=None),
        ),
        migrations.AlterUniqueTogether(
            name='method',
            unique_together=set([]),
        ),
        migrations.AlterUniqueTogether(
            name='processinglevel',
            unique_together=set([]),
        ),
        migrations.AlterUniqueTogether(
            name='site',
            unique_together=set([]),
        ),
        migrations.AlterUniqueTogether(
            name='timeseriesresult',
            unique_together=set([]),
        ),
        migrations.AlterUniqueTogether(
            name='variable',
            unique_together=set([]),
        ),
    ]
