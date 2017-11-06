# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hs_geographic_feature_resource', '0001_initial'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='originalfileinfo',
            unique_together=set([]),
        ),
        migrations.RemoveField(
            model_name='originalfileinfo',
            name='content_type',
        ),
        migrations.DeleteModel(
            name='OriginalFileInfo',
        ),
    ]
