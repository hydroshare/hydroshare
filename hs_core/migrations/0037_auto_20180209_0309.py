# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hs_core', '0036_auto_20171117_0422'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='externalprofilelink',
            unique_together=set([]),
        ),
        migrations.RemoveField(
            model_name='externalprofilelink',
            name='content_type',
        ),
        migrations.DeleteModel(
            name='ExternalProfileLink',
        ),
    ]
