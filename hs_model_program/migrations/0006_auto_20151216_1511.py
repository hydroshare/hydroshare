# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hs_model_program', '0005_auto_20151104_1604'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='mpmetadata',
            unique_together=set([]),
        ),
    ]
