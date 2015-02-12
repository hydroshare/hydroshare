# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hs_rhessys_inst_resource', '0006_modelrun_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='modelrun',
            name='description',
            field=models.CharField(max_length=1024, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='modelrun',
            name='title',
            field=models.CharField(default='Placeholder title', max_length=64),
            preserve_default=False,
        ),
    ]
