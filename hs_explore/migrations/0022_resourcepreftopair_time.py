# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hs_explore', '0021_grouppreftopair_state'),
    ]

    operations = [
        migrations.AddField(
            model_name='resourcepreftopair',
            name='time',
            field=models.IntegerField(default=0),
            preserve_default=False,
        ),
    ]
