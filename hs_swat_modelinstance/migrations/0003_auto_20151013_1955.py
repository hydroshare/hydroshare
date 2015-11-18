# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hs_core', '0006_auto_20150917_1515'),
        ('hs_model_program', '0003_auto_20150813_1730'),
        ('hs_swat_modelinstance', '0002_auto_20150813_1726'),
    ]

    operations = [
        migrations.CreateModel(
            name='SWATModelInstanceResource',
            fields=[
            ],
            options={
                'ordering': ('_order',),
                'verbose_name': 'SWAT Model Instance Resource',
                'proxy': True,
            },
            bases=('hs_core.baseresource',),
        ),
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
