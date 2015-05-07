# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hs_modelinstance', '0003_auto_20150506_2310'),
    ]

    operations = [
        migrations.RenameField(
            model_name='executedby',
            old_name='name',
            new_name='model_name',
        ),
    ]
