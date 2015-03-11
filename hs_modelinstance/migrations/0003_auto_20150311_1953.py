# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hs_modelinstance', '0002_auto_20150310_1927'),
    ]

    operations = [
        migrations.AlterField(
            model_name='modeloutput',
            name='includes_output',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
    ]
