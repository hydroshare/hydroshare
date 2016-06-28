# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hs_modflow_modelinstance', '0005_auto_20160628_1729'),
    ]

    operations = [
        migrations.RenameField(
            model_name='boundarycondition',
            old_name='headDependentFluxBoundaryPackages',
            new_name='head_dependent_flux_boundary_packages',
        ),
        migrations.RenameField(
            model_name='boundarycondition',
            old_name='specifiedFluxBoundaryPackages',
            new_name='specified_flux_boundary_packages',
        ),
        migrations.RenameField(
            model_name='boundarycondition',
            old_name='specifiedHeadBoundaryPackages',
            new_name='specified_head_boundary_packages',
        ),
        migrations.RenameField(
            model_name='generalelements',
            old_name='outputControlPackage',
            new_name='output_control_package',
        ),
    ]
