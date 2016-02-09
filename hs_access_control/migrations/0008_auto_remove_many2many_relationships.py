# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hs_access_control', '0007_manual_populate_new_fields'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='groupaccess',
            name='held_resources',
        ),
        migrations.RemoveField(
            model_name='groupaccess',
            name='members',
        ),
        migrations.RemoveField(
            model_name='resourceaccess',
            name='holding_groups',
        ),
        migrations.RemoveField(
            model_name='resourceaccess',
            name='holding_users',
        ),
        migrations.RemoveField(
            model_name='useraccess',
            name='held_groups',
        ),
        migrations.RemoveField(
            model_name='useraccess',
            name='held_resources',
        ),
    ]
