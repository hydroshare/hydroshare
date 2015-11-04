# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hs_access_control', '0003_auto_20150824_2215'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='useraccess',
            name='admin',
        ),
    ]
