# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hs_access_control', '0010_auto_rename_related_names'),
    ]

    operations = [
        migrations.RenameField(
            model_name='groupresourceprivilege',
            old_name='grantornew',
            new_name='grantor',
        ),
        migrations.RenameField(
            model_name='groupresourceprivilege',
            old_name='groupnew',
            new_name='group',
        ),
        migrations.RenameField(
            model_name='groupresourceprivilege',
            old_name='resourcenew',
            new_name='resource',
        ),
        migrations.RenameField(
            model_name='usergroupprivilege',
            old_name='grantornew',
            new_name='grantor',
        ),
        migrations.RenameField(
            model_name='usergroupprivilege',
            old_name='groupnew',
            new_name='group',
        ),
        migrations.RenameField(
            model_name='usergroupprivilege',
            old_name='usernew',
            new_name='user',
        ),
        migrations.RenameField(
            model_name='userresourceprivilege',
            old_name='grantornew',
            new_name='grantor',
        ),
        migrations.RenameField(
            model_name='userresourceprivilege',
            old_name='resourcenew',
            new_name='resource',
        ),
        migrations.RenameField(
            model_name='userresourceprivilege',
            old_name='usernew',
            new_name='user',
        ),
    ]
