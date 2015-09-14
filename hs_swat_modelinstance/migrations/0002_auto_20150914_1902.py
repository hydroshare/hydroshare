# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hs_model_program', '0001_initial'),
        ('hs_swat_modelinstance', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='executedby',
            name='name',
        ),
        migrations.RemoveField(
            model_name='executedby',
            name='url',
        ),
        migrations.AddField(
            model_name='executedby',
            name='model_name',
            field=models.CharField(default=None, max_length=500, choices=[(b'-', b'    ')]),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='executedby',
            name='model_program_fk',
            field=models.ForeignKey(related_name='swatmodelinstance', blank=True, to='hs_model_program.ModelProgramResource', null=True),
            preserve_default=True,
        ),
    ]
