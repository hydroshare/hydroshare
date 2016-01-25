# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hs_modelinstance', '0005_auto_20151111_2129'),
    ]

    operations = [
        migrations.AlterField(
            model_name='executedby',
            name='model_name',
            field=models.CharField(default=None, max_length=500),
            preserve_default=True,
        ),
    ]
