# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hs_core', '0017_auto_20160217_1629'),
    ]

    operations = [
        migrations.AddField(
            model_name='baseresource',
            name='locked',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
    ]
