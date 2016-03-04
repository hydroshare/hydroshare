# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hs_modflow_modelinstance', '0002_executedby_modeloutput_modflowmodelinstancemetadata_modflowmodelinstanceresource'),
    ]

    operations = [
        migrations.AlterField(
            model_name='boundarycondition',
            name='boundaryConditionPackage',
            field=models.ManyToManyField(to='hs_modflow_modelinstance.BoundaryConditionPackageChoices', null=True, verbose_name=b'Package(s)', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='boundarycondition',
            name='boundaryConditionType',
            field=models.ManyToManyField(to='hs_modflow_modelinstance.BoundaryConditionTypeChoices', null=True, verbose_name=b'Type(s)', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='generalelements',
            name='modelParameter',
            field=models.CharField(max_length=200, null=True, verbose_name=b'Model parameter(s)', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='generalelements',
            name='modelSolver',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name=b'Model solver', choices=[(b'DE4', b'DE4'), (b'GMG', b'GMG'), (b'LMG', b'LMG'), (b'PCG', b'PCG'), (b'PCGN', b'PCGN'), (b'SIP', b'SIP'), (b'SOR', b'SOR'), (b'NWT', b'NWT')]),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='generalelements',
            name='outputControlPackage',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name=b'Output control package', choices=[(b'GAGE', b'GAGE'), (b'HYD', b'HYD'), (b'LMT6', b'LMT6'), (b'MNWI', b'MNWI'), (b'OC', b'OC')]),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='generalelements',
            name='subsidencePackage',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name=b'Subsidence package', choices=[(b'IBS', b'IBS'), (b'SUB', b'SUB'), (b'SWT', b'SWT')]),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='griddimensions',
            name='numberOfColumns',
            field=models.CharField(max_length=100, null=True, verbose_name=b'Number of columns', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='griddimensions',
            name='numberOfLayers',
            field=models.CharField(max_length=100, null=True, verbose_name=b'Number of layers', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='griddimensions',
            name='numberOfRows',
            field=models.CharField(max_length=100, null=True, verbose_name=b'Number of rows', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='griddimensions',
            name='typeOfColumns',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name=b'Type of columns', choices=[(b'Regular', b'Regular'), (b'Irregular', b'Irregular')]),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='griddimensions',
            name='typeOfRows',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name=b'Type of rows', choices=[(b'Regular', b'Regular'), (b'Irregular', b'Irregular')]),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='groundwaterflow',
            name='flowPackage',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name=b'Flow package', choices=[(b'BCF6', b'BCF6'), (b'LPF', b'LPF'), (b'HUF2', b'HUF2'), (b'UPW', b'UPW'), (b'HFB6', b'HFB6'), (b'UZF', b'UZF'), (b'SWI2', b'SWI2')]),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='groundwaterflow',
            name='flowParameter',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name=b'Flow parameter', choices=[(b'Hydraulic Conductivity', b'Hydraulic Conductivity'), (b'Transmissivity', b'Transmissivity')]),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='modelcalibration',
            name='calibratedParameter',
            field=models.CharField(max_length=200, null=True, verbose_name=b'Calibrated parameter(s)', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='modelcalibration',
            name='calibrationMethod',
            field=models.CharField(max_length=200, null=True, verbose_name=b'Calibration method(s)', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='modelcalibration',
            name='observationProcessPackage',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name=b'Observation process package', choices=[(b'ADV2', b'ADV2'), (b'CHOB', b'CHOB'), (b'DROB', b'DROB'), (b'DTOB', b'DTOB'), (b'GBOB', b'GBOB'), (b'HOB', b'HOB'), (b'OBS', b'OBS'), (b'RVOB', b'RVOB'), (b'STOB', b'STOB')]),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='modelcalibration',
            name='observationType',
            field=models.CharField(max_length=200, null=True, verbose_name=b'Observation type(s)', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='modelinput',
            name='inputSourceName',
            field=models.CharField(max_length=200, null=True, verbose_name=b'Source name', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='modelinput',
            name='inputSourceURL',
            field=models.URLField(null=True, verbose_name=b'Source URL', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='modelinput',
            name='inputType',
            field=models.CharField(max_length=200, null=True, verbose_name=b'Type', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='stressperiod',
            name='stressPeriodType',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name=b'Type', choices=[(b'Steady', b'Steady'), (b'Transient', b'Transient'), (b'Steady and Transient', b'Steady and Transient')]),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='stressperiod',
            name='transientStateValueType',
            field=models.CharField(max_length=100, null=True, verbose_name=b'Type of transient state stress period(s)', choices=[(b'Annually', b'Annually'), (b'Monthly', b'Monthly'), (b'Daily', b'Daily'), (b'Hourly', b'Hourly')]),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='studyarea',
            name='maximumElevation',
            field=models.CharField(max_length=100, null=True, verbose_name=b'Maximum elevation in meters', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='studyarea',
            name='minimumElevation',
            field=models.CharField(max_length=100, null=True, verbose_name=b'Minimum elevation in meters', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='studyarea',
            name='totalLength',
            field=models.CharField(max_length=100, null=True, verbose_name=b'Total length in meters', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='studyarea',
            name='totalWidth',
            field=models.CharField(max_length=100, null=True, verbose_name=b'Total width in meters', blank=True),
            preserve_default=True,
        ),
    ]
