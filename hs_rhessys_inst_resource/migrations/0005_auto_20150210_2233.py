# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hs_core', '0002_auto_20150206_1720'),
        ('hs_rhessys_inst_resource', '0004_auto_20150210_2145'),
    ]

    operations = [
        migrations.AddField(
            model_name='modelrun',
            name='date_finished',
            field=models.DateTimeField(null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='modelrun',
            name='date_started',
            field=models.DateTimeField(null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='modelrun',
            name='model_results',
            field=models.ForeignKey(blank=True, to='hs_core.GenericResource', null=True),
            preserve_default=True,
        ),
    ]
