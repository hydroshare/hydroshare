# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hs_core', '0018_merge'),
    ]

    operations = [
        migrations.AddField(
            model_name='baseresource',
            name='locked_time',
            field=models.DateTimeField(null=True, blank=True),
        ),
    ]
