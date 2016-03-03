# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hs_core', '0016_merge'),
    ]

    operations = [
        migrations.AlterField(
            model_name='contributor',
            name='email',
            field=models.EmailField(max_length=254, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='creator',
            name='email',
            field=models.EmailField(max_length=254, null=True, blank=True),
        ),
    ]
