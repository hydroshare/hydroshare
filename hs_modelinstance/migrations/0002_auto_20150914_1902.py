# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hs_modelinstance', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='executedby',
            name='model_name',
            field=models.CharField(default=None, max_length=500, choices=[(b'-', b'    ')]),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='executedby',
            name='model_program_fk',
            field=models.ForeignKey(related_name='modelinstance', blank=True, to='hs_model_program.ModelProgramResource', null=True),
            preserve_default=True,
        ),
    ]
