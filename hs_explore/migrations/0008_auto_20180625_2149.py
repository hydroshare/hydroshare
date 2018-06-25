# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hs_explore', '0007_auto_20180625_2101'),
    ]

    operations = [
        migrations.RenameField(
            model_name='recommendedgroup',
            old_name='keys',
            new_name='keywords',
        ),
        migrations.RenameField(
            model_name='recommendedresource',
            old_name='relations',
            new_name='keywords',
        ),
        migrations.RenameField(
            model_name='recommendeduser',
            old_name='keys',
            new_name='keywords',
        ),
    ]
