# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hs_swat_modelinstance', '0006_auto_20160114_1508'),
    ]

    operations = [
        migrations.AlterField(
            model_name='modelobjective',
            name='swat_model_objectives',
            field=models.ManyToManyField(to='hs_swat_modelinstance.ModelObjectiveChoices', blank=True),
        ),
        migrations.AlterField(
            model_name='modelparameter',
            name='model_parameters',
            field=models.ManyToManyField(to='hs_swat_modelinstance.ModelParametersChoices', blank=True),
        ),
    ]
