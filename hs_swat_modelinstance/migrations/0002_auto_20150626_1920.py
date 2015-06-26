# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hs_swat_modelinstance', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ModelObjectiveChoices',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('description', models.CharField(max_length=300)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.RemoveField(
            model_name='modelobjective',
            name='swat_model_objective',
        ),
        migrations.RemoveField(
            model_name='swatmodelparameters',
            name='has_crop_rotation',
        ),
        migrations.RemoveField(
            model_name='swatmodelparameters',
            name='has_fertilizer',
        ),
        migrations.RemoveField(
            model_name='swatmodelparameters',
            name='has_inlet_of_draining_watershed',
        ),
        migrations.RemoveField(
            model_name='swatmodelparameters',
            name='has_irrigation_operation',
        ),
        migrations.RemoveField(
            model_name='swatmodelparameters',
            name='has_point_source',
        ),
        migrations.RemoveField(
            model_name='swatmodelparameters',
            name='has_tillage_operation',
        ),
        migrations.RemoveField(
            model_name='swatmodelparameters',
            name='has_title_drainage',
        ),
        migrations.AddField(
            model_name='modelinput',
            name='routing_time_step',
            field=models.CharField(max_length=100, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='modelinput',
            name='warm_up_period',
            field=models.CharField(max_length=100, null=True, verbose_name=b'Warm-up period in years', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='modelobjective',
            name='swat_model_objectives',
            field=models.ManyToManyField(to='hs_swat_modelinstance.ModelObjectiveChoices', null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='swatmodelparameters',
            name='model_parameters',
            field=models.CharField(max_length=100, null=True, choices=[(b'Crop rotation', b'Crop rotation'), (b'Tile drainage', b'Tile drainage'), (b'Point source', b'Point source'), (b'Fertilizer', b'Fertilizer'), (b'Tillage operation', b'Tillage operation'), (b'Inlet of draining watershed', b'Inlet of draining watershed'), (b'Irrigation operation', b'Irrigation operation')]),
            preserve_default=True,
        ),
    ]
