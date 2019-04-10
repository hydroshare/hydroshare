# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hs_dictionary', '0002_auto_20170824_1900'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='university',
            options={'verbose_name_plural': 'universities'},
        ),
    ]
