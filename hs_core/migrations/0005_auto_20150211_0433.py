# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hs_core', '0004_auto_20150210_1628'),
    ]

    operations = [
        migrations.AlterField(
            model_name='format',
            name='value',
            field=models.CharField(max_length=150),
            preserve_default=True,
        ),
    ]
