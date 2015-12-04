# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hs_core', '0006_auto_20150917_1515'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='format',
            unique_together=set([('value', 'content_type', 'object_id')]),
        ),
    ]
