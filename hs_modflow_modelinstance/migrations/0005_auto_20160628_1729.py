# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hs_modflow_modelinstance', '0004_auto_20160627_1929'),
    ]

    operations = [
        migrations.CreateModel(
            name='SpecifiedHeadBoundaryPackageChoices',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('description', models.CharField(max_length=300)),
            ],
        ),
        migrations.RenameModel(
            old_name='BoundaryConditionPackageChoices',
            new_name='HeadDependentFluxBoundaryPackageChoices',
        ),
        migrations.RenameModel(
            old_name='BoundaryConditionTypeChoices',
            new_name='SpecifiedFluxBoundaryPackageChoices',
        ),
        migrations.RemoveField(
            model_name='boundarycondition',
            name='boundaryConditionPackage',
        ),
        migrations.RemoveField(
            model_name='boundarycondition',
            name='boundaryConditionType',
        ),
        migrations.AddField(
            model_name='boundarycondition',
            name='headDependentFluxBoundaryPackages',
            field=models.ManyToManyField(to='hs_modflow_modelinstance.HeadDependentFluxBoundaryPackageChoices', blank=True),
        ),
        migrations.AddField(
            model_name='boundarycondition',
            name='specifiedFluxBoundaryPackages',
            field=models.ManyToManyField(to='hs_modflow_modelinstance.SpecifiedFluxBoundaryPackageChoices', blank=True),
        ),
        migrations.AlterField(
            model_name='generalelements',
            name='outputControlPackage',
            field=models.ManyToManyField(to='hs_modflow_modelinstance.OutputControlPackageChoices', blank=True),
        ),
        migrations.AddField(
            model_name='boundarycondition',
            name='specifiedHeadBoundaryPackages',
            field=models.ManyToManyField(to='hs_modflow_modelinstance.SpecifiedHeadBoundaryPackageChoices', blank=True),
        ),
    ]
