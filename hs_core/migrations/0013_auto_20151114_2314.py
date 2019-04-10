# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hs_core', '0012_auto_20151114_2243'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='coverage',
            unique_together=set([('type', 'content_type', 'object_id')]),
        ),
    ]
