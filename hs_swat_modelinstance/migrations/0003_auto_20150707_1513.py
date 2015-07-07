# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0001_initial'),
        ('hs_swat_modelinstance', '0002_auto_20150626_1920'),
    ]

    operations = [
        migrations.CreateModel(
            name='ModelMethod',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('runoff_calculation_method', models.CharField(max_length=200, null=True, blank=True)),
                ('flow_routing_method', models.CharField(max_length=200, null=True, blank=True)),
                ('PET_estimation_method', models.CharField(max_length=200, null=True, blank=True)),
                ('content_type', models.ForeignKey(related_name='hs_swat_modelinstance_modelmethod_related', to='contenttypes.ContentType')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ModelParameter',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('other_parameters', models.CharField(max_length=200, null=True, blank=True)),
                ('content_type', models.ForeignKey(related_name='hs_swat_modelinstance_modelparameter_related', to='contenttypes.ContentType')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ModelParametersChoices',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('description', models.CharField(max_length=300)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.RemoveField(
            model_name='modelmethods',
            name='content_type',
        ),
        migrations.DeleteModel(
            name='ModelMethods',
        ),
        migrations.RemoveField(
            model_name='swatmodelparameters',
            name='content_type',
        ),
        migrations.DeleteModel(
            name='SWATModelParameters',
        ),
        migrations.AddField(
            model_name='modelparameter',
            name='model_parameters',
            field=models.ManyToManyField(to='hs_swat_modelinstance.ModelParametersChoices', null=True, blank=True),
            preserve_default=True,
        ),
        migrations.RenameField(
            model_name='modelinput',
            old_name='rainfall_time_step',
            new_name='rainfall_time_step_value',
        ),
        migrations.RenameField(
            model_name='modelinput',
            old_name='routing_time_step',
            new_name='routing_time_step_value',
        ),
        migrations.RenameField(
            model_name='modelinput',
            old_name='simulation_time_step',
            new_name='simulation_time_step_value',
        ),
        migrations.AddField(
            model_name='modelinput',
            name='rainfall_time_step_type',
            field=models.CharField(blank=True, max_length=100, null=True, choices=[(b'Daily', b'Daily'), (b'Sub-hourly', b'Sub-hourly')]),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='modelinput',
            name='routing_time_step_type',
            field=models.CharField(blank=True, max_length=100, null=True, choices=[(b'Daily', b'Daily'), (b'Hourly', b'Hourly')]),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='modelinput',
            name='simulation_time_step_type',
            field=models.CharField(blank=True, max_length=100, null=True, choices=[(b'Annual', b'Annual'), (b'Monthly', b'Monthly'), (b'Daily', b'Daily'), (b'Hourly', b'Hourly')]),
            preserve_default=True,
        ),
    ]
