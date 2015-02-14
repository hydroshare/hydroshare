# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hs_rhessys_inst_resource', '0009_modelrunoptions'),
    ]

    operations = [
        migrations.AddField(
            model_name='modelrunoptions',
            name='name',
            field=models.CharField(default='', max_length=64),
            preserve_default=False,
        ),
    ]
