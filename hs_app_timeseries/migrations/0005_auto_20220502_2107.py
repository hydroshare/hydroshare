# -*- coding: utf-8 -*-
# Generated by Django 1.11.29 on 2022-05-02 21:07
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hs_app_timeseries', '0004_auto_20220502_1850'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='cvaggregationstatistic',
            name='metadata',
        ),
        migrations.RemoveField(
            model_name='cvelevationdatum',
            name='metadata',
        ),
        migrations.RemoveField(
            model_name='cvmedium',
            name='metadata',
        ),
        migrations.RemoveField(
            model_name='cvmethodtype',
            name='metadata',
        ),
        migrations.RemoveField(
            model_name='cvsitetype',
            name='metadata',
        ),
        migrations.RemoveField(
            model_name='cvspeciation',
            name='metadata',
        ),
        migrations.RemoveField(
            model_name='cvstatus',
            name='metadata',
        ),
        migrations.RemoveField(
            model_name='cvunitstype',
            name='metadata',
        ),
        migrations.RemoveField(
            model_name='cvvariablename',
            name='metadata',
        ),
        migrations.RemoveField(
            model_name='cvvariabletype',
            name='metadata',
        ),
        migrations.RemoveField(
            model_name='timeseriesmetadata',
            name='coremetadata_ptr',
        ),
        migrations.DeleteModel(
            name='CVAggregationStatistic',
        ),
        migrations.DeleteModel(
            name='CVElevationDatum',
        ),
        migrations.DeleteModel(
            name='CVMedium',
        ),
        migrations.DeleteModel(
            name='CVMethodType',
        ),
        migrations.DeleteModel(
            name='CVStatus',
        ),
        migrations.DeleteModel(
            name='CVUnitsType',
        ),
        migrations.DeleteModel(
            name='CVSiteType',
        ),
        migrations.DeleteModel(
            name='CVSpeciation',
        ),
        migrations.DeleteModel(
            name='CVVariableName',
        ),
        migrations.DeleteModel(
            name='CVVariableType',
        ),
        migrations.DeleteModel(
            name='TimeSeriesResource',
        ),
        migrations.DeleteModel(
            name='TimeSeriesMetaData',
        ),
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.RemoveField(
                    model_name='method',
                    name='content_type',
                ),
                migrations.RemoveField(
                    model_name='processinglevel',
                    name='content_type',
                ),
                migrations.RemoveField(
                    model_name='site',
                    name='content_type',
                ),
                migrations.RemoveField(
                    model_name='timeseriesresult',
                    name='content_type',
                ),
                migrations.RemoveField(
                    model_name='utcoffset',
                    name='content_type',
                ),
                migrations.RemoveField(
                    model_name='variabletimeseries',
                    name='content_type',
                ),
                migrations.DeleteModel(
                    name='Method',
                ),
                migrations.DeleteModel(
                    name='ProcessingLevel',
                ),
                migrations.DeleteModel(
                    name='Site',
                ),
                migrations.DeleteModel(
                    name='TimeSeriesResult',
                ),
                migrations.DeleteModel(
                    name='UTCOffSet',
                ),
                migrations.DeleteModel(
                    name='VariableTimeseries',
                ),
            ],
            database_operations=[
                migrations.AlterModelTable(
                    name='Method',
                    table='hs_file_types_method',
                ),
                migrations.AlterModelTable(
                    name='Site',
                    table='hs_file_types_site',
                ),
                migrations.AlterModelTable(
                    name='TimeSeriesResult',
                    table='hs_file_types_timeseriesresult',
                ),
                migrations.AlterModelTable(
                    name='UTCOffSet',
                    table='hs_file_types_utcoffset',
                ),
                migrations.AlterModelTable(
                    name='ProcessingLevel',
                    table='hs_file_types_processinglevel',
                ),
                migrations.AlterModelTable(
                    name='VariableTimeseries',
                    table='hs_file_types_variabletimeseries',
                ),
            ],
        )
    ]