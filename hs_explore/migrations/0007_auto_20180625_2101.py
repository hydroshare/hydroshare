# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hs_explore', '0006_auto_20180625_2027'),
    ]

    operations = [
        migrations.RenameField(
            model_name='recommendedresource',
            old_name='keys',
            new_name='relations',
        ),
    ]
