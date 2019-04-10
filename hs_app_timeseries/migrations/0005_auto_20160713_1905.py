# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.contrib.postgres.fields


class Migration(migrations.Migration):

    dependencies = [
        ('hs_app_timeseries', '0004_auto_20160526_2026'),
    ]

    operations = [
        migrations.CreateModel(
            name='CVAggregationStatistic',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('term', models.CharField(max_length=255)),
                ('name', models.CharField(max_length=255)),
                ('is_dirty', models.BooleanField(default=False)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='CVElevationDatum',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('term', models.CharField(max_length=255)),
                ('name', models.CharField(max_length=255)),
                ('is_dirty', models.BooleanField(default=False)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='CVMedium',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('term', models.CharField(max_length=255)),
                ('name', models.CharField(max_length=255)),
                ('is_dirty', models.BooleanField(default=False)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='CVMethodType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('term', models.CharField(max_length=255)),
                ('name', models.CharField(max_length=255)),
                ('is_dirty', models.BooleanField(default=False)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='CVSiteType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('term', models.CharField(max_length=255)),
                ('name', models.CharField(max_length=255)),
                ('is_dirty', models.BooleanField(default=False)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='CVSpeciation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('term', models.CharField(max_length=255)),
                ('name', models.CharField(max_length=255)),
                ('is_dirty', models.BooleanField(default=False)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='CVStatus',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('term', models.CharField(max_length=255)),
                ('name', models.CharField(max_length=255)),
                ('is_dirty', models.BooleanField(default=False)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='CVUnitsType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('term', models.CharField(max_length=255)),
                ('name', models.CharField(max_length=255)),
                ('is_dirty', models.BooleanField(default=False)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='CVVariableName',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('term', models.CharField(max_length=255)),
                ('name', models.CharField(max_length=255)),
                ('is_dirty', models.BooleanField(default=False)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='CVVariableType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('term', models.CharField(max_length=255)),
                ('name', models.CharField(max_length=255)),
                ('is_dirty', models.BooleanField(default=False)),
            ],
            options={
                'abstract': False,
            },
        ),
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
            model_name='timeseriesmetadata',
            name='is_dirty',
            field=models.BooleanField(default=False),
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
        migrations.AddField(
            model_name='cvvariabletype',
            name='metadata',
            field=models.ForeignKey(related_name='cv_variable_types', to='hs_app_timeseries.TimeSeriesMetaData'),
        ),
        migrations.AddField(
            model_name='cvvariablename',
            name='metadata',
            field=models.ForeignKey(related_name='cv_variable_names', to='hs_app_timeseries.TimeSeriesMetaData'),
        ),
        migrations.AddField(
            model_name='cvunitstype',
            name='metadata',
            field=models.ForeignKey(related_name='cv_units_types', to='hs_app_timeseries.TimeSeriesMetaData'),
        ),
        migrations.AddField(
            model_name='cvstatus',
            name='metadata',
            field=models.ForeignKey(related_name='cv_statuses', to='hs_app_timeseries.TimeSeriesMetaData'),
        ),
        migrations.AddField(
            model_name='cvspeciation',
            name='metadata',
            field=models.ForeignKey(related_name='cv_speciations', to='hs_app_timeseries.TimeSeriesMetaData'),
        ),
        migrations.AddField(
            model_name='cvsitetype',
            name='metadata',
            field=models.ForeignKey(related_name='cv_site_types', to='hs_app_timeseries.TimeSeriesMetaData'),
        ),
        migrations.AddField(
            model_name='cvmethodtype',
            name='metadata',
            field=models.ForeignKey(related_name='cv_method_types', to='hs_app_timeseries.TimeSeriesMetaData'),
        ),
        migrations.AddField(
            model_name='cvmedium',
            name='metadata',
            field=models.ForeignKey(related_name='cv_mediums', to='hs_app_timeseries.TimeSeriesMetaData'),
        ),
        migrations.AddField(
            model_name='cvelevationdatum',
            name='metadata',
            field=models.ForeignKey(related_name='cv_elevation_datums', to='hs_app_timeseries.TimeSeriesMetaData'),
        ),
        migrations.AddField(
            model_name='cvaggregationstatistic',
            name='metadata',
            field=models.ForeignKey(related_name='cv_aggregation_statistics', to='hs_app_timeseries.TimeSeriesMetaData'),
        ),
    ]
