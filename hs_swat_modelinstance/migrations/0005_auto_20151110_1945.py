# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hs_modelinstance', '0004_auto_20151110_1920'),
        ('hs_swat_modelinstance', '0004_auto_20151106_1932'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='executedby',
            name='content_type',
        ),
        migrations.RemoveField(
            model_name='executedby',
            name='model_program_fk',
        ),
        migrations.DeleteModel(
            name='ExecutedBy',
        ),
        migrations.RemoveField(
            model_name='modeloutput',
            name='content_type',
        ),
        migrations.DeleteModel(
            name='ModelOutput',
        ),
        migrations.CreateModel(
            name='ExecutedBy',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('hs_modelinstance.executedby',),
        ),
        migrations.CreateModel(
            name='ModelOutput',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('hs_modelinstance.modeloutput',),
        ),
        migrations.RemoveField(
            model_name='swatmodelinstancemetadata',
            name='coremetadata_ptr',
        ),
        migrations.AddField(
            model_name='swatmodelinstancemetadata',
            name='modelinstancemetadata_ptr',
            field=models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, default=0, serialize=False, to='hs_modelinstance.ModelInstanceMetaData'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='modelinput',
            name='demSourceName',
            field=models.CharField(max_length=200, null=True, verbose_name=b'DEM source name', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='modelinput',
            name='demSourceURL',
            field=models.URLField(null=True, verbose_name=b'DEM source URL', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='modelinput',
            name='landUseDataSourceName',
            field=models.CharField(max_length=200, null=True, verbose_name=b'LandUse data source name', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='modelinput',
            name='landUseDataSourceURL',
            field=models.URLField(null=True, verbose_name=b'LandUse data source URL', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='modelinput',
            name='numberOfHRUs',
            field=models.CharField(max_length=100, null=True, verbose_name=b'Number of HRUs', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='modelinput',
            name='numberOfSubbasins',
            field=models.CharField(max_length=100, null=True, verbose_name=b'Number of subbasins', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='modelinput',
            name='rainfallTimeStepType',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name=b'Rainfall time step type', choices=[(b'Daily', b'Daily'), (b'Sub-hourly', b'Sub-hourly')]),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='modelinput',
            name='rainfallTimeStepValue',
            field=models.CharField(max_length=100, null=True, verbose_name=b'Rainfall time step value', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='modelinput',
            name='routingTimeStepType',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name=b'Routing time step type', choices=[(b'Daily', b'Daily'), (b'Hourly', b'Hourly')]),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='modelinput',
            name='routingTimeStepValue',
            field=models.CharField(max_length=100, null=True, verbose_name=b'Routing time step value', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='modelinput',
            name='simulationTimeStepType',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name=b'Simulation time step type', choices=[(b'Annual', b'Annual'), (b'Monthly', b'Monthly'), (b'Daily', b'Daily'), (b'Hourly', b'Hourly')]),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='modelinput',
            name='simulationTimeStepValue',
            field=models.CharField(max_length=100, null=True, verbose_name=b'Simulation time step value', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='modelinput',
            name='soilDataSourceName',
            field=models.CharField(max_length=200, null=True, verbose_name=b'Soil data source name', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='modelinput',
            name='soilDataSourceURL',
            field=models.URLField(null=True, verbose_name=b'Soil data source URL', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='modelmethod',
            name='flowRoutingMethod',
            field=models.CharField(max_length=200, null=True, verbose_name=b'Flow routing method', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='modelmethod',
            name='petEstimationMethod',
            field=models.CharField(max_length=200, null=True, verbose_name=b'PET estimation method', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='modelmethod',
            name='runoffCalculationMethod',
            field=models.CharField(max_length=200, null=True, verbose_name=b'Runoff calculation method', blank=True),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='modelinput',
            unique_together=set([('content_type', 'object_id')]),
        ),
        migrations.AlterUniqueTogether(
            name='modelmethod',
            unique_together=set([('content_type', 'object_id')]),
        ),
        migrations.AlterUniqueTogether(
            name='modelobjective',
            unique_together=set([('content_type', 'object_id')]),
        ),
        migrations.AlterUniqueTogether(
            name='modelparameter',
            unique_together=set([('content_type', 'object_id')]),
        ),
        migrations.AlterUniqueTogether(
            name='simulationtype',
            unique_together=set([('content_type', 'object_id')]),
        ),
    ]
