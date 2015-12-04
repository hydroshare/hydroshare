# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hs_modelinstance', '0003_merge'),
    ]

    operations = [
        migrations.AlterField(
            model_name='executedby',
            name='model_program_fk',
            field=models.ForeignKey(related_name='modelinstance', default=None, blank=True, to='hs_model_program.ModelProgramResource', null=True),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='executedby',
            unique_together=set([('content_type', 'object_id')]),
        ),
        migrations.AlterUniqueTogether(
            name='modeloutput',
            unique_together=set([('content_type', 'object_id')]),
        ),
    ]
