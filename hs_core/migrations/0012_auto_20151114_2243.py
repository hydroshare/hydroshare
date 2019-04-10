# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hs_core', '0011_auto_20151114_2231'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='date',
            unique_together=set([('type', 'content_type', 'object_id')]),
        ),
    ]
