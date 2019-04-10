# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hs_core', '0014_auto_20151123_1451'),
    ]

    operations = [
        migrations.AddField(
            model_name='baseresource',
            name='file_unpack_message',
            field=models.TextField(null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='baseresource',
            name='file_unpack_status',
            field=models.CharField(blank=True, max_length=7, null=True, choices=[(b'Pending', b'Pending'), (b'Running', b'Running'), (b'Done', b'Done'), (b'Error', b'Error')]),
            preserve_default=True,
        ),
    ]
