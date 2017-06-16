# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings
import hs_core.models


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0001_initial'),
        ('pages', '__first__'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('contenttypes', '0001_initial'),
        ('hs_core', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ExecutedBy',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('name', models.CharField(max_length=200)),
                ('url', models.URLField()),
                ('content_type', models.ForeignKey(related_name='hs_swat_modelinstance_executedby_related', to='contenttypes.ContentType')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ModelInput',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('warm_up_period', models.CharField(max_length=100, null=True, verbose_name=b'Warm-up period in years', blank=True)),
                ('rainfall_time_step_type', models.CharField(blank=True, max_length=100, null=True, choices=[(b'Daily', b'Daily'), (b'Sub-hourly', b'Sub-hourly')])),
                ('rainfall_time_step_value', models.CharField(max_length=100, null=True, blank=True)),
                ('routing_time_step_type', models.CharField(blank=True, max_length=100, null=True, choices=[(b'Daily', b'Daily'), (b'Hourly', b'Hourly')])),
                ('routing_time_step_value', models.CharField(max_length=100, null=True, blank=True)),
                ('simulation_time_step_type', models.CharField(blank=True, max_length=100, null=True, choices=[(b'Annual', b'Annual'), (b'Monthly', b'Monthly'), (b'Daily', b'Daily'), (b'Hourly', b'Hourly')])),
                ('simulation_time_step_value', models.CharField(max_length=100, null=True, blank=True)),
                ('watershed_area', models.CharField(max_length=100, null=True, verbose_name=b'Waterhsed area in square kilometers', blank=True)),
                ('number_of_subbasins', models.CharField(max_length=100, null=True, blank=True)),
                ('number_of_HRUs', models.CharField(max_length=100, null=True, blank=True)),
                ('DEM_resolution', models.CharField(max_length=100, null=True, verbose_name=b'DEM resolution in meters', blank=True)),
                ('DEM_source_name', models.CharField(max_length=200, null=True, blank=True)),
                ('DEM_source_URL', models.URLField(null=True, blank=True)),
                ('landUse_data_source_name', models.CharField(max_length=200, null=True, blank=True)),
                ('landUse_data_source_URL', models.URLField(null=True, blank=True)),
                ('soil_data_source_name', models.CharField(max_length=200, null=True, blank=True)),
                ('soil_data_source_URL', models.URLField(null=True, blank=True)),
                ('content_type', models.ForeignKey(related_name='hs_swat_modelinstance_modelinput_related', to='contenttypes.ContentType')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
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
            name='ModelObjective',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('other_objectives', models.CharField(max_length=200, null=True, blank=True)),
                ('content_type', models.ForeignKey(related_name='hs_swat_modelinstance_modelobjective_related', to='contenttypes.ContentType')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
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
        migrations.CreateModel(
            name='ModelOutput',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('includes_output', models.BooleanField(default=False)),
                ('content_type', models.ForeignKey(related_name='hs_swat_modelinstance_modeloutput_related', to='contenttypes.ContentType')),
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
        migrations.CreateModel(
            name='SimulationType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('simulation_type_name', models.CharField(max_length=100, verbose_name=b'Simulation type', choices=[(b'Normal Simulation', b'Normal Simulation'), (b'Sensitivity Analysis', b'Sensitivity Analysis'), (b'Auto-Calibration', b'Auto-Calibration')])),
                ('content_type', models.ForeignKey(related_name='hs_swat_modelinstance_simulationtype_related', to='contenttypes.ContentType')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='SWATModelInstanceMetaData',
            fields=[
                ('coremetadata_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='hs_core.CoreMetaData')),
            ],
            options={
            },
            bases=('hs_core.coremetadata',),
        ),
        migrations.CreateModel(
            name='SWATModelInstanceResource',
            fields=[
                ('page_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='pages.Page')),
                ('comments_count', models.IntegerField(default=0, editable=False)),
                ('rating_count', models.IntegerField(default=0, editable=False)),
                ('rating_sum', models.IntegerField(default=0, editable=False)),
                ('rating_average', models.FloatField(default=0, editable=False)),
                ('public', models.BooleanField(default=True, help_text=b'If this is true, the resource is viewable and downloadable by anyone')),
                ('frozen', models.BooleanField(default=False, help_text=b'If this is true, the resource should not be modified')),
                ('do_not_distribute', models.BooleanField(default=False, help_text=b'If this is true, the resource owner has to designate viewers')),
                ('discoverable', models.BooleanField(default=True, help_text=b'If this is true, it will turn up in searches.')),
                ('published_and_frozen', models.BooleanField(default=False, help_text=b'Once this is true, no changes can be made to the resource')),
                ('content', models.TextField()),
                ('short_id', models.CharField(default=hs_core.models.short_id, max_length=32, db_index=True)),
                ('doi', models.CharField(help_text=b"Permanent identifier. Never changes once it's been set.", max_length=1024, null=True, db_index=True, blank=True)),
                ('object_id', models.PositiveIntegerField(null=True, blank=True)),
                ('content_type', models.ForeignKey(blank=True, to='contenttypes.ContentType', null=True)),
                ('creator', models.ForeignKey(related_name='creator_of_hs_swat_modelinstance_swatmodelinstanceresource', to=settings.AUTH_USER_MODEL, help_text=b'This is the person who first uploaded the resource')),
                ('edit_groups', models.ManyToManyField(help_text=b'This is the set of xDCIShare Groups who can edit the resource', related_name='group_editable_hs_swat_modelinstance_swatmodelinstanceresource', null=True, to='auth.Group', blank=True)),
                ('edit_users', models.ManyToManyField(help_text=b'This is the set of xDCIShare Users who can edit the resource', related_name='user_editable_hs_swat_modelinstance_swatmodelinstanceresource', null=True, to=settings.AUTH_USER_MODEL, blank=True)),
                ('last_changed_by', models.ForeignKey(related_name='last_changed_hs_swat_modelinstance_swatmodelinstanceresource', to=settings.AUTH_USER_MODEL, help_text=b'The person who last changed the resource', null=True)),
                ('owners', models.ManyToManyField(help_text=b'The person who has total ownership of the resource', related_name='owns_hs_swat_modelinstance_swatmodelinstanceresource', to=settings.AUTH_USER_MODEL)),
                ('user', models.ForeignKey(related_name='swatmodelinstanceresources', verbose_name='Author', to=settings.AUTH_USER_MODEL)),
                ('view_groups', models.ManyToManyField(help_text=b'This is the set of xDCIShare Groups who can view the resource', related_name='group_viewable_hs_swat_modelinstance_swatmodelinstanceresource', null=True, to='auth.Group', blank=True)),
                ('view_users', models.ManyToManyField(help_text=b'This is the set of xDCIShare Users who can view the resource', related_name='user_viewable_hs_swat_modelinstance_swatmodelinstanceresource', null=True, to=settings.AUTH_USER_MODEL, blank=True)),
            ],
            options={
                'ordering': ('_order',),
                'verbose_name': 'SWAT Model Instance Resource',
            },
            bases=('pages.page', models.Model),
        ),
        migrations.AddField(
            model_name='modelparameter',
            name='model_parameters',
            field=models.ManyToManyField(to='hs_swat_modelinstance.ModelParametersChoices', null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='modelobjective',
            name='swat_model_objectives',
            field=models.ManyToManyField(to='hs_swat_modelinstance.ModelObjectiveChoices', null=True, blank=True),
            preserve_default=True,
        ),
    ]
