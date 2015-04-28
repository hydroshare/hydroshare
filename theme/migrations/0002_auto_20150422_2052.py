# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('theme', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='organization',
            field=models.CharField(help_text=b'The name of the organization you work for.', max_length=1024, null=True, blank=True),
            preserve_default=True,
        ),
    ]
