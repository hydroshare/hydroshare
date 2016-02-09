# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('hs_app_timeseries', '0001_initial'),
        ('hs_core', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='TimeSeriesMetaData',
            fields=[
                ('coremetadata_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='hs_core.CoreMetaData')),
            ],
            bases=('hs_core.coremetadata',),
        ),
        migrations.CreateModel(
            name='TimeSeriesResult',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('units_type', models.CharField(max_length=255)),
                ('units_name', models.CharField(max_length=255)),
                ('units_abbreviation', models.CharField(max_length=20)),
                ('status', models.CharField(max_length=255)),
                ('sample_medium', models.CharField(max_length=255)),
                ('value_count', models.IntegerField()),
                ('aggregation_statistics', models.CharField(max_length=255)),
                ('content_type', models.ForeignKey(related_name='hs_app_timeseries_timeseriesresult_related', to='contenttypes.ContentType')),
            ],
        ),
        migrations.CreateModel(
            name='Variable',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('variable_code', models.CharField(max_length=20)),
                ('variable_name', models.CharField(max_length=100)),
                ('variable_type', models.CharField(max_length=100)),
                ('no_data_value', models.IntegerField()),
                ('variable_definition', models.CharField(max_length=255, null=True, blank=True)),
                ('speciation', models.CharField(max_length=255, null=True, blank=True)),
                ('content_type', models.ForeignKey(related_name='hs_app_timeseries_variable_related', to='contenttypes.ContentType')),
            ],
        ),
        migrations.CreateModel(
            name='TimeSeriesResource',
            fields=[
            ],
            options={
                'ordering': ('_order',),
                'verbose_name': 'Time Series',
                'proxy': True,
            },
            bases=('hs_core.baseresource',),
        ),
        migrations.AddField(
            model_name='site',
            name='content_type',
            field=models.ForeignKey(related_name='hs_app_timeseries_site_related', to='contenttypes.ContentType'),
        ),
        migrations.AddField(
            model_name='processinglevel',
            name='content_type',
            field=models.ForeignKey(related_name='hs_app_timeseries_processinglevel_related', to='contenttypes.ContentType'),
        ),
        migrations.AddField(
            model_name='method',
            name='content_type',
            field=models.ForeignKey(related_name='hs_app_timeseries_method_related', to='contenttypes.ContentType'),
        ),
        migrations.AlterUniqueTogether(
            name='variable',
            unique_together=set([('content_type', 'object_id')]),
        ),
        migrations.AlterUniqueTogether(
            name='timeseriesresult',
            unique_together=set([('content_type', 'object_id')]),
        ),
        migrations.AlterUniqueTogether(
            name='site',
            unique_together=set([('content_type', 'object_id')]),
        ),
        migrations.AlterUniqueTogether(
            name='processinglevel',
            unique_together=set([('content_type', 'object_id')]),
        ),
        migrations.AlterUniqueTogether(
            name='method',
            unique_together=set([('content_type', 'object_id')]),
        ),
    ]
