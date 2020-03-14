# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='BoundaryCondition',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('other_specified_head_boundary_packages', models.CharField(max_length=200, null=True, verbose_name='Other packages', blank=True)),
                ('other_specified_flux_boundary_packages', models.CharField(max_length=200, null=True, verbose_name='Other packages', blank=True)),
                ('other_head_dependent_flux_boundary_packages', models.CharField(max_length=200, null=True, verbose_name='Other packages', blank=True)),
                ('content_type', models.ForeignKey(related_name='hs_modflow_modelinstance_boundarycondition_related', to='contenttypes.ContentType')),
            ],
        ),
        migrations.CreateModel(
            name='GeneralElements',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('modelParameter', models.CharField(max_length=200, null=True, verbose_name='Model parameter(s)', blank=True)),
                ('modelSolver', models.CharField(blank=True, max_length=100, null=True, verbose_name='Model solver', choices=[('DE4', 'DE4'), ('GMG', 'GMG'), ('LMG', 'LMG'), ('PCG', 'PCG'), ('PCGN', 'PCGN'), ('SIP', 'SIP'), ('SOR', 'SOR'), ('NWT', 'NWT')])),
                ('subsidencePackage', models.CharField(blank=True, max_length=100, null=True, verbose_name='Subsidence package', choices=[('IBS', 'IBS'), ('SU', 'SU'), ('SWT', 'SWT')])),
                ('content_type', models.ForeignKey(related_name='hs_modflow_modelinstance_generalelements_related', to='contenttypes.ContentType')),
            ],
        ),
        migrations.CreateModel(
            name='GridDimensions',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('numberOfLayers', models.CharField(max_length=100, null=True, verbose_name='Number of layers', blank=True)),
                ('typeOfRows', models.CharField(blank=True, max_length=100, null=True, verbose_name='Type of rows', choices=[('Regular', 'Regular'), ('Irregular', 'Irregular')])),
                ('numberOfRows', models.CharField(max_length=100, null=True, verbose_name='Number of rows', blank=True)),
                ('typeOfColumns', models.CharField(blank=True, max_length=100, null=True, verbose_name='Type of columns', choices=[('Regular', 'Regular'), ('Irregular', 'Irregular')])),
                ('numberOfColumns', models.CharField(max_length=100, null=True, verbose_name='Number of columns', blank=True)),
                ('content_type', models.ForeignKey(related_name='hs_modflow_modelinstance_griddimensions_related', to='contenttypes.ContentType')),
            ],
        ),
        migrations.CreateModel(
            name='GroundWaterFlow',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('flowPackage', models.CharField(blank=True, max_length=100, null=True, verbose_name='Flow package', choices=[('BCF6', 'BCF6'), ('LPF', 'LPF'), ('HUF2', 'HUF2'), ('UPW', 'UPW'), ('HFB6', 'HFB6'), ('UZF', 'UZF'), ('SWI2', 'SWI2')])),
                ('flowParameter', models.CharField(blank=True, max_length=100, null=True, verbose_name='Flow parameter', choices=[('Hydraulic Conductivity', 'Hydraulic Conductivity'), ('Transmissivity', 'Transmissivity')])),
                ('content_type', models.ForeignKey(related_name='hs_modflow_modelinstance_groundwaterflow_related', to='contenttypes.ContentType')),
            ],
        ),
        migrations.CreateModel(
            name='HeadDependentFluxBoundaryPackageChoices',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('description', models.CharField(max_length=300)),
            ],
        ),
        migrations.CreateModel(
            name='ModelCalibration',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('calibratedParameter', models.CharField(max_length=200, null=True, verbose_name='Calibrated parameter(s)', blank=True)),
                ('observationType', models.CharField(max_length=200, null=True, verbose_name='Observation type(s)', blank=True)),
                ('observationProcessPackage', models.CharField(blank=True, max_length=100, null=True, verbose_name='Observation process package', choices=[('ADV2', 'ADV2'), ('CHO', 'CHO'), ('DRO', 'DRO'), ('DTO', 'DTO'), ('GBO', 'GBO'), ('HO', 'HO'), ('OBS', 'OBS'), ('RVO', 'RVO'), ('STO', 'STO')])),
                ('calibrationMethod', models.CharField(max_length=200, null=True, verbose_name='Calibration method(s)', blank=True)),
                ('content_type', models.ForeignKey(related_name='hs_modflow_modelinstance_modelcalibration_related', to='contenttypes.ContentType')),
            ],
        ),
        migrations.CreateModel(
            name='ModelInput',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('inputType', models.CharField(max_length=200, null=True, verbose_name='Type', blank=True)),
                ('inputSourceName', models.CharField(max_length=200, null=True, verbose_name='Source name', blank=True)),
                ('inputSourceURL', models.URLField(null=True, verbose_name='Source URL', blank=True)),
                ('content_type', models.ForeignKey(related_name='hs_modflow_modelinstance_modelinput_related', to='contenttypes.ContentType')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='OutputControlPackageChoices',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('description', models.CharField(max_length=300)),
            ],
        ),
        migrations.CreateModel(
            name='SpecifiedFluxBoundaryPackageChoices',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('description', models.CharField(max_length=300)),
            ],
        ),
        migrations.CreateModel(
            name='SpecifiedHeadBoundaryPackageChoices',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('description', models.CharField(max_length=300)),
            ],
        ),
        migrations.CreateModel(
            name='StressPeriod',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('stressPeriodType', models.CharField(blank=True, max_length=100, null=True, verbose_name='Type', choices=[('Steady', 'Steady'), ('Transient', 'Transient'), ('Steady and Transient', 'Steady and Transient')])),
                ('steadyStateValue', models.CharField(max_length=100, null=True, verbose_name='Length of steady state stress period(s)', blank=True)),
                ('transientStateValueType', models.CharField(max_length=100, null=True, verbose_name='Type of transient state stress period(s)', choices=[('Annually', 'Annually'), ('Monthly', 'Monthly'), ('Daily', 'Daily'), ('Hourly', 'Hourly'), ('Other', 'Other')])),
                ('transientStateValue', models.CharField(max_length=100, null=True, verbose_name='Length of transient state stress period(s)', blank=True)),
                ('content_type', models.ForeignKey(related_name='hs_modflow_modelinstance_stressperiod_related', to='contenttypes.ContentType')),
            ],
        ),
        migrations.CreateModel(
            name='StudyArea',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('totalLength', models.CharField(max_length=100, null=True, verbose_name='Total length in meters', blank=True)),
                ('totalWidth', models.CharField(max_length=100, null=True, verbose_name='Total width in meters', blank=True)),
                ('maximumElevation', models.CharField(max_length=100, null=True, verbose_name='Maximum elevation in meters', blank=True)),
                ('minimumElevation', models.CharField(max_length=100, null=True, verbose_name='Minimum elevation in meters', blank=True)),
                ('content_type', models.ForeignKey(related_name='hs_modflow_modelinstance_studyarea_related', to='contenttypes.ContentType')),
            ],
        ),
        migrations.AddField(
            model_name='generalelements',
            name='output_control_package',
            field=models.ManyToManyField(to='hs_modflow_modelinstance.OutputControlPackageChoices', blank=True),
        ),
        migrations.AddField(
            model_name='boundarycondition',
            name='head_dependent_flux_boundary_packages',
            field=models.ManyToManyField(to='hs_modflow_modelinstance.HeadDependentFluxBoundaryPackageChoices', blank=True),
        ),
        migrations.AddField(
            model_name='boundarycondition',
            name='specified_flux_boundary_packages',
            field=models.ManyToManyField(to='hs_modflow_modelinstance.SpecifiedFluxBoundaryPackageChoices', blank=True),
        ),
        migrations.AddField(
            model_name='boundarycondition',
            name='specified_head_boundary_packages',
            field=models.ManyToManyField(to='hs_modflow_modelinstance.SpecifiedHeadBoundaryPackageChoices', blank=True),
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
        migrations.AlterUniqueTogether(
            name='boundarycondition',
            unique_together=set([('content_type', 'object_id')]),
        ),
    ]
