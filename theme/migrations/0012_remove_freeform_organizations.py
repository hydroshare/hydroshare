# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('theme', '0011_create_existing_organizations'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='userprofile',
            name='organization',
        ),
        migrations.RenameField(
            model_name='userprofile',
            old_name='_organization',
            new_name='organization',
        ),
    ]
