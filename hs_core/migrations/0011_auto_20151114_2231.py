# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hs_core', '0010_auto_20151114_2205'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='relation',
            unique_together=set([('type', 'content_type', 'object_id')]),
        ),
    ]
