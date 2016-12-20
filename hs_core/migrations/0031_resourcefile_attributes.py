# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django_irods.storage
import hs_core.models


class Migration(migrations.Migration):

    dependencies = [
        ('hs_core', '0030_resourcefile_file_folder'),
    ]

    operations = [
        migrations.AlterField(
            model_name='resourcefile',
            name='fed_resource_file',
            field=models.FileField(storage=hs_core.models.FedStorage(), max_length=4096, null=True, upload_to=hs_core.models.get_path, blank=True),
        ),
        migrations.AlterField(
            model_name='resourcefile',
            name='file_folder',
            field=models.CharField(max_length=4096, null=True),
        ),
        migrations.AlterField(
            model_name='resourcefile',
            name='resource_file',
            field=models.FileField(storage=django_irods.storage.IrodsStorage(), max_length=4096, null=True, upload_to=hs_core.models.get_path, blank=True),
        ),
    ]
