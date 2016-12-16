# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hs_core', '0029_auto_20161123_1858'),
    ]

    operations = [
        migrations.AddField(
            model_name='resourcefile',
            name='file_folder',
            field=models.CharField(max_length=4096, null=True),
        ),
    ]
