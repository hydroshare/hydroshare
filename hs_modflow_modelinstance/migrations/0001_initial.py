# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='BoundaryCondition',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='BoundaryConditionPackageChoices',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('description', models.CharField(max_length=300)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='BoundaryConditionTypeChoices',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('description', models.CharField(max_length=300)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='GeneralElements',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('modelParameter', models.CharField(max_length=200, null=True, blank=True)),
                ('modelSolver', models.CharField(blank=True, max_length=100, null=True, choices=[(b'DE4', b'DE4'), (b'GMG', b'GMG'), (b'LMG', b'LMG'), (b'PCG', b'PCG'), (b'PCGN', b'PCGN'), (b'SIP', b'SIP'), (b'SOR', b'SOR'), (b'NWT', b'NWT')])),
                ('outputControlPackage', models.CharField(blank=True, max_length=100, null=True, choices=[(b'GAGE', b'GAGE'), (b'HYD', b'HYD'), (b'LMT6', b'LMT6'), (b'MNWI', b'MNWI'), (b'OC', b'OC')])),
                ('subsidencePackage', models.CharField(blank=True, max_length=100, null=True, choices=[(b'IBS', b'IBS'), (b'SUB', b'SUB'), (b'SWT', b'SWT')])),
                ('content_type', models.ForeignKey(related_name='hs_modflow_modelinstance_generalelements_related', to='contenttypes.ContentType')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='GridDimensions',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('numberOfLayers', models.CharField(max_length=100, null=True, verbose_name=b'Number of model grid layers', blank=True)),
                ('typeOfRows', models.CharField(blank=True, max_length=100, null=True, choices=[(b'Regular', b'Regular'), (b'Irregular', b'Irregular')])),
                ('numberOfRows', models.CharField(max_length=100, null=True, blank=True)),
                ('typeOfColumns', models.CharField(blank=True, max_length=100, null=True, choices=[(b'Regular', b'Regular'), (b'Irregular', b'Irregular')])),
                ('numberOfColumns', models.CharField(max_length=100, null=True, blank=True)),
                ('content_type', models.ForeignKey(related_name='hs_modflow_modelinstance_griddimensions_related', to='contenttypes.ContentType')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='GroundWaterFlow',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('flowPackage', models.CharField(blank=True, max_length=100, null=True, choices=[(b'BCF6', b'BCF6'), (b'LPF', b'LPF'), (b'HUF2', b'HUF2'), (b'UPW', b'UPW'), (b'HFB6', b'HFB6'), (b'UZF', b'UZF'), (b'SWI2', b'SWI2')])),
                ('flowParameter', models.CharField(blank=True, max_length=100, null=True, choices=[(b'Hydraulic Conductivity', b'Hydraulic Conductivity'), (b'Transmissivity', b'Transmissivity')])),
                ('content_type', models.ForeignKey(related_name='hs_modflow_modelinstance_groundwaterflow_related', to='contenttypes.ContentType')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ModelCalibration',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('calibratedParameter', models.CharField(max_length=200, null=True, blank=True)),
                ('observationType', models.CharField(max_length=200, null=True, blank=True)),
                ('observationProcessPackage', models.CharField(blank=True, max_length=100, null=True, choices=[(b'ADV2', b'ADV2'), (b'CHOB', b'CHOB'), (b'DROB', b'DROB'), (b'DTOB', b'DTOB'), (b'GBOB', b'GBOB'), (b'HOB', b'HOB'), (b'OBS', b'OBS'), (b'RVOB', b'RVOB'), (b'STOB', b'STOB')])),
                ('calibrationMethod', models.CharField(max_length=200, null=True, blank=True)),
                ('content_type', models.ForeignKey(related_name='hs_modflow_modelinstance_modelcalibration_related', to='contenttypes.ContentType')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ModelInput',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('inputType', models.CharField(max_length=200, null=True, blank=True)),
                ('inputSourceName', models.CharField(max_length=200, null=True, blank=True)),
                ('inputSourceURL', models.URLField(null=True, verbose_name=b'Input source URL', blank=True)),
                ('content_type', models.ForeignKey(related_name='hs_modflow_modelinstance_modelinput_related', to='contenttypes.ContentType')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='StressPeriod',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('stressPeriodType', models.CharField(blank=True, max_length=100, null=True, choices=[(b'Steady', b'Steady'), (b'Transient', b'Transient'), (b'Steady and Transient', b'Steady and Transient')])),
                ('steadyStateValue', models.CharField(max_length=100, null=True, verbose_name=b'Length of steady state stress period(s)', blank=True)),
                ('transientStateValueType', models.CharField(max_length=100, null=True, choices=[(b'Annually', b'Annually'), (b'Monthly', b'Monthly'), (b'Daily', b'Daily'), (b'Hourly', b'Hourly')])),
                ('transientStateValue', models.CharField(max_length=100, null=True, verbose_name=b'Length of transient state stress period(s)', blank=True)),
                ('content_type', models.ForeignKey(related_name='hs_modflow_modelinstance_stressperiod_related', to='contenttypes.ContentType')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='StudyArea',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('totalLength', models.CharField(max_length=100, null=True, verbose_name=b'Study area total length in meters', blank=True)),
                ('totalWidth', models.CharField(max_length=100, null=True, verbose_name=b'Study area total width in meters', blank=True)),
                ('maximumElevation', models.CharField(max_length=100, null=True, verbose_name=b'Study area maximum elevation in meters', blank=True)),
                ('minimumElevation', models.CharField(max_length=100, null=True, verbose_name=b'Study area minimum elevation in meters', blank=True)),
                ('content_type', models.ForeignKey(related_name='hs_modflow_modelinstance_studyarea_related', to='contenttypes.ContentType')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='studyarea',
            unique_together=set([('content_type', 'object_id')]),
        ),
        migrations.AlterUniqueTogether(
            name='stressperiod',
            unique_together=set([('content_type', 'object_id')]),
        ),
        migrations.AlterUniqueTogether(
            name='modelcalibration',
            unique_together=set([('content_type', 'object_id')]),
        ),
        migrations.AlterUniqueTogether(
            name='groundwaterflow',
            unique_together=set([('content_type', 'object_id')]),
        ),
        migrations.AlterUniqueTogether(
            name='griddimensions',
            unique_together=set([('content_type', 'object_id')]),
        ),
        migrations.AlterUniqueTogether(
            name='generalelements',
            unique_together=set([('content_type', 'object_id')]),
        ),
        migrations.AddField(
            model_name='boundarycondition',
            name='boundaryConditionPackage',
            field=models.ManyToManyField(to='hs_modflow_modelinstance.BoundaryConditionPackageChoices', null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='boundarycondition',
            name='boundaryConditionType',
            field=models.ManyToManyField(to='hs_modflow_modelinstance.BoundaryConditionTypeChoices', null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='boundarycondition',
            name='content_type',
            field=models.ForeignKey(related_name='hs_modflow_modelinstance_boundarycondition_related', to='contenttypes.ContentType'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='boundarycondition',
            unique_together=set([('content_type', 'object_id')]),
        ),
    ]
