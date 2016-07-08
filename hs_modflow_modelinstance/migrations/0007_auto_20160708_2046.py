# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hs_modflow_modelinstance', '0006_auto_20160628_1811'),
    ]

    operations = [
        migrations.AddField(
            model_name='boundarycondition',
            name='other_head_dependent_flux_boundary_packages',
            field=models.CharField(max_length=200, null=True, verbose_name=b'Other packages', blank=True),
        ),
        migrations.AddField(
            model_name='boundarycondition',
            name='other_specified_flux_boundary_packages',
            field=models.CharField(max_length=200, null=True, verbose_name=b'Other packages', blank=True),
        ),
        migrations.AddField(
            model_name='boundarycondition',
            name='other_specified_head_boundary_packages',
            field=models.CharField(max_length=200, null=True, verbose_name=b'Other packages', blank=True),
        ),
        migrations.AlterField(
            model_name='stressperiod',
            name='transientStateValueType',
            field=models.CharField(max_length=100, null=True, verbose_name=b'Type of transient state stress period(s)', choices=[(b'Annually', b'Annually'), (b'Monthly', b'Monthly'), (b'Daily', b'Daily'), (b'Hourly', b'Hourly'), (b'Other', b'Other')]),
        ),
    ]
