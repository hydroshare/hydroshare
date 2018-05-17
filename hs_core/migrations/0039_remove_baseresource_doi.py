# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hs_core', '0038_baseresource_minid'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='baseresource',
            name='doi',
        ),
    ]
