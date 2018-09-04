# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hs_explore', '0024_auto_20180827_1954'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='grouppreftopair',
            name='state',
        ),
    ]
