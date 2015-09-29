# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hs_core', '0001_initial'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='externalprofilelink',
            unique_together=None,
        ),
        migrations.RemoveField(
            model_name='externalprofilelink',
            name='content_type',
        ),
        migrations.DeleteModel(
            name='ExternalProfileLink',
        ),
    ]
