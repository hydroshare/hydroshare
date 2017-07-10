# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hs_core', '0035_remove_deprecated_fields'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='baseresource',
            name='comments_count',
        ),
    ]
