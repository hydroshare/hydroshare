# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hs_access_control', '0021_auto_20170506_1538'),
    ]

    operations = [
        migrations.AddField(
            model_name='resourceaccess',
            name='require_download_agreement',
            field=models.BooleanField(default=False, help_text=b'whether to require agreement to resource rights statement for resource content downloads'),
        ),
    ]
