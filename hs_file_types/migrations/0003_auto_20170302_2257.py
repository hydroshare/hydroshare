# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hs_file_types', '0002_auto_20170216_1904'),
    ]

    operations = [
        migrations.AddField(
            model_name='genericfilemetadata',
            name='is_dirty',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='georasterfilemetadata',
            name='is_dirty',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='netcdffilemetadata',
            name='is_dirty',
            field=models.BooleanField(default=False),
        ),
    ]
