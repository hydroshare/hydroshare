# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django_irods.storage
import hs_core.models


class Migration(migrations.Migration):

    dependencies = [
        ('hs_core', '0024_baseresource_resource_federation_path'),
    ]

    operations = [
        migrations.AddField(
            model_name='resourcefile',
            name='fed_resource_file',
            field=models.FileField(storage=django_irods.storage.IrodsStorage(b'federated'), max_length=500, null=True, upload_to=hs_core.models.get_path, blank=True),
        ),
    ]
