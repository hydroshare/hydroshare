# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ref_ts', '0004_auto_20151124_2303'),
    ]

    operations = [
        migrations.AddField(
            model_name='site',
            name='net_work',
            field=models.CharField(default=b'', max_length=100),
            preserve_default=True,
        ),
    ]
