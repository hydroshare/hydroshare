# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('hs_model_program', '0004_auto_20150506_2310'),
        ('hs_modelinstance', '0002_auto_20150313_1656'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='executedby',
            name='url',
        ),
        migrations.AddField(
            model_name='executedby',
            name='model_program_fk',
            field=models.ForeignKey(blank=True, to='hs_model_program.ModelProgramResource', null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='executedby',
            name='name',
            field=models.CharField(max_length=500, choices=[(b'-', b'    ')]),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='modelinstanceresource',
            name='owners',
            field=models.ManyToManyField(help_text=b'The person who has total ownership of the resource', related_name='owns_hs_modelinstance_modelinstanceresource', to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
    ]
