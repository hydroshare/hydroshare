# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hs_tools_resource', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='fee',
            name='content_type',
        ),
        migrations.DeleteModel(
            name='Fee',
        ),
        migrations.AddField(
            model_name='requesturlbase',
            name='resShortID',
            field=models.CharField(default=b'UNKNOWN', max_length=100),
            preserve_default=True,
        ),
    ]
