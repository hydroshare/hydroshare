# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hs_core', '0019_baseresource_locked_time'),
    ]

    operations = [
        migrations.AddField(
            model_name='baseresource',
            name='collections',
            field=models.ManyToManyField(related_name='resources', to='hs_core.BaseResource'),
        ),
    ]
