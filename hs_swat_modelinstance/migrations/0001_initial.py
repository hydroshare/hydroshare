# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('hs_modelinstance', '0001_initial'),
        ('hs_core', '__first__'),
    ]

    operations = [
        migrations.CreateModel(
            name='ModelInput',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('warmupPeriodValue', models.CharField(max_length=100, null=True, verbose_name=b'Warm-up period in years', blank=True)),
                ('rainfallTimeStepType', models.CharField(blank=True, max_length=100, null=True, verbose_name=b'Rainfall time step type', choices=[(b'Daily', b'Daily'), (b'Sub-hourly', b'Sub-hourly')])),
                ('rainfallTimeStepValue', models.CharField(max_length=100, null=True, verbose_name=b'Rainfall time step value', blank=True)),
                ('routingTimeStepType', models.CharField(blank=True, max_length=100, null=True, verbose_name=b'Routing time step type', choices=[(b'Daily', b'Daily'), (b'Hourly', b'Hourly')])),
                ('routingTimeStepValue', models.CharField(max_length=100, null=True, verbose_name=b'Routing time step value', blank=True)),
                ('simulationTimeStepType', models.CharField(blank=True, max_length=100, null=True, verbose_name=b'Simulation time step type', choices=[(b'Annual', b'Annual'), (b'Monthly', b'Monthly'), (b'Daily', b'Daily'), (b'Hourly', b'Hourly')])),
                ('simulationTimeStepValue', models.CharField(max_length=100, null=True, verbose_name=b'Simulation time step value', blank=True)),
                ('watershedArea', models.CharField(max_length=100, null=True, verbose_name=b'Watershed area in square kilometers', blank=True)),
                ('numberOfSubbasins', models.CharField(max_length=100, null=True, verbose_name=b'Number of subbasins', blank=True)),
                ('numberOfHRUs', models.CharField(max_length=100, null=True, verbose_name=b'Number of HRUs', blank=True)),
                ('demResolution', models.CharField(max_length=100, null=True, verbose_name=b'DEM resolution in meters', blank=True)),
                ('demSourceName', models.CharField(max_length=200, null=True, verbose_name=b'DEM source name', blank=True)),
                ('demSourceURL', models.URLField(null=True, verbose_name=b'DEM source URL', blank=True)),
                ('landUseDataSourceName', models.CharField(max_length=200, null=True, verbose_name=b'LandUse data source name', blank=True)),
                ('landUseDataSourceURL', models.URLField(null=True, verbose_name=b'LandUse data source URL', blank=True)),
                ('soilDataSourceName', models.CharField(max_length=200, null=True, verbose_name=b'Soil data source name', blank=True)),
                ('soilDataSourceURL', models.URLField(null=True, verbose_name=b'Soil data source URL', blank=True)),
                ('content_type', models.ForeignKey(related_name='hs_swat_modelinstance_modelinput_related', to='contenttypes.ContentType')),
            ],
        ),
        migrations.CreateModel(
            name='ModelMethod',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('runoffCalculationMethod', models.CharField(max_length=200, null=True, verbose_name=b'Runoff calculation method', blank=True)),
                ('flowRoutingMethod', models.CharField(max_length=200, null=True, verbose_name=b'Flow routing method', blank=True)),
                ('petEstimationMethod', models.CharField(max_length=200, null=True, verbose_name=b'PET estimation method', blank=True)),
                ('content_type', models.ForeignKey(related_name='hs_swat_modelinstance_modelmethod_related', to='contenttypes.ContentType')),
            ],
        ),
        migrations.CreateModel(
            name='ModelObjective',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('other_objectives', models.CharField(max_length=200, null=True, blank=True)),
                ('content_type', models.ForeignKey(related_name='hs_swat_modelinstance_modelobjective_related', to='contenttypes.ContentType')),
            ],
        ),
        migrations.CreateModel(
            name='ModelObjectiveChoices',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('description', models.CharField(max_length=300)),
            ],
        ),
        migrations.CreateModel(
            name='ModelParameter',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('other_parameters', models.CharField(max_length=200, null=True, blank=True)),
                ('content_type', models.ForeignKey(related_name='hs_swat_modelinstance_modelparameter_related', to='contenttypes.ContentType')),
            ],
        ),
        migrations.CreateModel(
            name='ModelParametersChoices',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('description', models.CharField(max_length=300)),
            ],
        ),
        migrations.CreateModel(
            name='SimulationType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('simulation_type_name', models.CharField(max_length=100, verbose_name=b'Simulation type', choices=[(b'Normal Simulation', b'Normal Simulation'), (b'Sensitivity Analysis', b'Sensitivity Analysis'), (b'Auto-Calibration', b'Auto-Calibration')])),
                ('content_type', models.ForeignKey(related_name='hs_swat_modelinstance_simulationtype_related', to='contenttypes.ContentType')),
            ],
        ),
        migrations.CreateModel(
            name='SWATModelInstanceMetaData',
            fields=[
                ('modelinstancemetadata_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='hs_modelinstance.ModelInstanceMetaData')),
            ],
            bases=('hs_modelinstance.modelinstancemetadata',),
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
        migrations.CreateModel(
            name='SWATModelInstanceResource',
            fields=[
            ],
            options={
                'ordering': ('_order',),
                'verbose_name': 'SWAT Model Instance Resource',
                'proxy': True,
            },
            bases=('hs_core.baseresource',),
        ),
        migrations.AddField(
            model_name='modelparameter',
            name='model_parameters',
            field=models.ManyToManyField(to='hs_swat_modelinstance.ModelParametersChoices', null=True, blank=True),
        ),
        migrations.AddField(
            model_name='modelobjective',
            name='swat_model_objectives',
            field=models.ManyToManyField(to='hs_swat_modelinstance.ModelObjectiveChoices', null=True, blank=True),
        ),
        migrations.AlterUniqueTogether(
            name='simulationtype',
            unique_together=set([('content_type', 'object_id')]),
        ),
        migrations.AlterUniqueTogether(
            name='modelparameter',
            unique_together=set([('content_type', 'object_id')]),
        ),
        migrations.AlterUniqueTogether(
            name='modelobjective',
            unique_together=set([('content_type', 'object_id')]),
        ),
        migrations.AlterUniqueTogether(
            name='modelmethod',
            unique_together=set([('content_type', 'object_id')]),
        ),
        migrations.AlterUniqueTogether(
            name='modelinput',
            unique_together=set([('content_type', 'object_id')]),
        ),
    ]
