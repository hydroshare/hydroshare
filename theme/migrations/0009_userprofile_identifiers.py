# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.contrib.postgres.fields.hstore


class Migration(migrations.Migration):

    dependencies = [
        ('theme', '0008_auto_20170622_2141'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='identifiers',
            field=django.contrib.postgres.fields.hstore.HStoreField(default={}, null=True, blank=True),
        ),
    ]
