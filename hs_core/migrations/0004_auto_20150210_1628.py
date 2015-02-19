# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django_irods.storage
import hs_core.models


class Migration(migrations.Migration):

    dependencies = [
        ('hs_core', '0003_auto_20150130_2158'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bags',
            name='bag',
            field=models.FileField(storage=django_irods.storage.IrodsStorage(), max_length=500, null=True, upload_to=b'bags'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='resourcefile',
            name='resource_file',
            field=models.FileField(storage=django_irods.storage.IrodsStorage(), max_length=500, upload_to=hs_core.models.get_path),
            preserve_default=True,
        ),
    ]
