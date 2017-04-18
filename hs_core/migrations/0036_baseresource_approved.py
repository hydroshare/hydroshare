# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hs_core', '0035_remove_deprecated_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='baseresource',
            name='approved',
            field=models.BooleanField(default=False),
        ),
    ]
