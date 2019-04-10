# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hs_swat_modelinstance', '0003_auto_20151013_1955'),
    ]

    operations = [
        migrations.RenameField(
            model_name='modelinput',
            old_name='DEM_resolution',
            new_name='demResolution',
        ),
        migrations.RenameField(
            model_name='modelinput',
            old_name='DEM_source_name',
            new_name='demSourceName',
        ),
        migrations.RenameField(
            model_name='modelinput',
            old_name='DEM_source_URL',
            new_name='demSourceURL',
        ),
        migrations.RenameField(
            model_name='modelinput',
            old_name='landUse_data_source_name',
            new_name='landUseDataSourceName',
        ),
        migrations.RenameField(
            model_name='modelinput',
            old_name='landUse_data_source_URL',
            new_name='landUseDataSourceURL',
        ),
        migrations.RenameField(
            model_name='modelinput',
            old_name='number_of_HRUs',
            new_name='numberOfHRUs',
        ),
        migrations.RenameField(
            model_name='modelinput',
            old_name='number_of_subbasins',
            new_name='numberOfSubbasins',
        ),
        migrations.RenameField(
            model_name='modelinput',
            old_name='rainfall_time_step_type',
            new_name='rainfallTimeStepType',
        ),
        migrations.RenameField(
            model_name='modelinput',
            old_name='rainfall_time_step_value',
            new_name='rainfallTimeStepValue',
        ),
        migrations.RenameField(
            model_name='modelinput',
            old_name='routing_time_step_type',
            new_name='routingTimeStepType',
        ),
        migrations.RenameField(
            model_name='modelinput',
            old_name='routing_time_step_value',
            new_name='routingTimeStepValue',
        ),
        migrations.RenameField(
            model_name='modelinput',
            old_name='simulation_time_step_type',
            new_name='simulationTimeStepType',
        ),
        migrations.RenameField(
            model_name='modelinput',
            old_name='simulation_time_step_value',
            new_name='simulationTimeStepValue',
        ),
        migrations.RenameField(
            model_name='modelinput',
            old_name='soil_data_source_name',
            new_name='soilDataSourceName',
        ),
        migrations.RenameField(
            model_name='modelinput',
            old_name='soil_data_source_URL',
            new_name='soilDataSourceURL',
        ),
        migrations.RenameField(
            model_name='modelinput',
            old_name='warm_up_period',
            new_name='warmupPeriodValue',
        ),
        migrations.RenameField(
            model_name='modelinput',
            old_name='watershed_area',
            new_name='watershedArea',
        ),
        migrations.RenameField(
            model_name='modelmethod',
            old_name='PET_estimation_method',
            new_name='flowRoutingMethod',
        ),
        migrations.RenameField(
            model_name='modelmethod',
            old_name='flow_routing_method',
            new_name='petEstimationMethod',
        ),
        migrations.RenameField(
            model_name='modelmethod',
            old_name='runoff_calculation_method',
            new_name='runoffCalculationMethod',
        ),
    ]
