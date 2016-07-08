# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hs_tracking', '0002_auto_20160406_1244'),
    ]

    operations = [
        migrations.AlterField(
            model_name='variable',
            name='type',
            field=models.IntegerField(choices=[(0, b'Integer'), (1, b'Floating Point'), (2, b'Text'), (3, b'Flag'), (4, b'None')]),
        ),
    ]
