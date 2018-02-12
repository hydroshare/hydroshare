# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('theme', '0008_auto_20170622_2141'),
    ]

    operations = [
        migrations.AddField(
            model_name='quotamessage',
            name='enforce_quota',
            field=models.BooleanField(default=False),
        ),
    ]
