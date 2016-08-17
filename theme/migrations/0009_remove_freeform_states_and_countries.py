# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import localflavor.us.models
import django_countries.fields


class Migration(migrations.Migration):

    dependencies = [
        ('theme', '0008_migrate_state_and_country'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='userprofile',
            name='country',
        ),
        migrations.RemoveField(
            model_name='userprofile',
            name='state',
        ),
        migrations.RenameField(
            model_name='userprofile',
            old_name='new_country',
            new_name='country',
        ),
        migrations.RenameField(
            model_name='userprofile',
            old_name='new_state',
            new_name='state',
        ),
    ]
