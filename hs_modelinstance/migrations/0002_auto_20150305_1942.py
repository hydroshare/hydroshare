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
            name='name',
            field=models.CharField(max_length=500, choices=[(b'-', b'    ')]),
            preserve_default=True,
        ),
    ]
