# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hs_core', '0009_auto_20151114_2105'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='language',
            unique_together=set([('content_type', 'object_id')]),
        ),
    ]
