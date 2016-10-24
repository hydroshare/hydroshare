# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.contrib.postgres.fields.hstore


class Migration(migrations.Migration):

    dependencies = [
        ('hs_core', '0027_auto_20160818_2308'),
    ]

    operations = [
        migrations.AddField(
            model_name='baseresource',
            name='extra_data',
            field=django.contrib.postgres.fields.hstore.HStoreField(default={}),
        ),
    ]
