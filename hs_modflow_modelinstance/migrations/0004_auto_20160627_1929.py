# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hs_modflow_modelinstance', '0003_auto_20160304_1816'),
    ]

    operations = [
        migrations.CreateModel(
            name='OutputControlPackageChoices',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('description', models.CharField(max_length=300)),
            ],
        ),
        migrations.AlterField(
            model_name='boundarycondition',
            name='boundaryConditionPackage',
            field=models.ManyToManyField(to='hs_modflow_modelinstance.BoundaryConditionPackageChoices', null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='boundarycondition',
            name='boundaryConditionType',
            field=models.ManyToManyField(to='hs_modflow_modelinstance.BoundaryConditionTypeChoices', null=True, blank=True),
        ),
        migrations.RemoveField(
            model_name='generalelements',
            name='outputControlPackage',
        ),
        migrations.AddField(
            model_name='generalelements',
            name='outputControlPackage',
            field=models.ManyToManyField(to='hs_modflow_modelinstance.OutputControlPackageChoices', null=True, blank=True),
        ),
    ]
