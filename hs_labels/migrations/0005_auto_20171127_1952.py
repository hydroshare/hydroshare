# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hs_labels', '0004_auto_add_constraints'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userresourceflags',
            name='kind',
            field=models.IntegerField(default=1, editable=False, choices=[(1, b'Favorite'), (2, b'Mine'), (3, b'Open With App')]),
        ),
    ]
