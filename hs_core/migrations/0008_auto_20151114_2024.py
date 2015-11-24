# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hs_core', '0007_auto_20151114_1618'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='subject',
            unique_together=set([('value', 'content_type', 'object_id')]),
        ),
    ]
