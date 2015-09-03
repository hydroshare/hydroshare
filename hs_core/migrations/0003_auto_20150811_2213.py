# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hs_core', '0002_auto_20150806_2145'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='groupaccess',
            name='group',
        ),
        migrations.RemoveField(
            model_name='groupaccess',
            name='held_resources',
        ),
        migrations.RemoveField(
            model_name='groupaccess',
            name='members',
        ),
        migrations.AlterUniqueTogether(
            name='groupresourceprivilege',
            unique_together=None,
        ),
        migrations.RemoveField(
            model_name='groupresourceprivilege',
            name='grantor',
        ),
        migrations.RemoveField(
            model_name='groupresourceprivilege',
            name='group',
        ),
        migrations.RemoveField(
            model_name='groupresourceprivilege',
            name='resource',
        ),
        migrations.RemoveField(
            model_name='resourceaccess',
            name='holding_groups',
        ),
        migrations.DeleteModel(
            name='GroupResourcePrivilege',
        ),
        migrations.RemoveField(
            model_name='resourceaccess',
            name='holding_users',
        ),
        migrations.RemoveField(
            model_name='resourceaccess',
            name='resource',
        ),
        migrations.RemoveField(
            model_name='useraccess',
            name='held_groups',
        ),
        migrations.RemoveField(
            model_name='useraccess',
            name='held_resources',
        ),
        migrations.RemoveField(
            model_name='useraccess',
            name='user',
        ),
        migrations.AlterUniqueTogether(
            name='usergroupprivilege',
            unique_together=None,
        ),
        migrations.RemoveField(
            model_name='usergroupprivilege',
            name='grantor',
        ),
        migrations.RemoveField(
            model_name='usergroupprivilege',
            name='group',
        ),
        migrations.DeleteModel(
            name='GroupAccess',
        ),
        migrations.RemoveField(
            model_name='usergroupprivilege',
            name='user',
        ),
        migrations.DeleteModel(
            name='UserGroupPrivilege',
        ),
        migrations.AlterUniqueTogether(
            name='userresourceprivilege',
            unique_together=None,
        ),
        migrations.RemoveField(
            model_name='userresourceprivilege',
            name='grantor',
        ),
        migrations.RemoveField(
            model_name='userresourceprivilege',
            name='resource',
        ),
        migrations.DeleteModel(
            name='ResourceAccess',
        ),
        migrations.RemoveField(
            model_name='userresourceprivilege',
            name='user',
        ),
        migrations.DeleteModel(
            name='UserAccess',
        ),
        migrations.DeleteModel(
            name='UserResourcePrivilege',
        ),
    ]
