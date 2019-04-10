# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hs_core', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='genericresource',
            name='resource_type',
            field=models.CharField(default=b'GenericResource', max_length=50),
            preserve_default=True,
        ),
    ]
