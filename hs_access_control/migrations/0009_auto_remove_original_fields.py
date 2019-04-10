# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hs_access_control', '0008_auto_remove_many2many_relationships'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='groupresourceprivilege',
            unique_together=set([]),
        ),
        migrations.RemoveField(
            model_name='groupresourceprivilege',
            name='resource',
        ),
        migrations.RemoveField(
            model_name='groupresourceprivilege',
            name='group',
        ),
        migrations.RemoveField(
            model_name='groupresourceprivilege',
            name='grantor',
        ),
        migrations.AlterUniqueTogether(
            name='usergroupprivilege',
            unique_together=set([]),
        ),
        migrations.RemoveField(
            model_name='usergroupprivilege',
            name='user',
        ),
        migrations.RemoveField(
            model_name='usergroupprivilege',
            name='group',
        ),
        migrations.RemoveField(
            model_name='usergroupprivilege',
            name='grantor',
        ),
        migrations.AlterUniqueTogether(
            name='userresourceprivilege',
            unique_together=set([]),
        ),
        migrations.RemoveField(
            model_name='userresourceprivilege',
            name='user',
        ),
        migrations.RemoveField(
            model_name='userresourceprivilege',
            name='resource',
        ),
        migrations.RemoveField(
            model_name='userresourceprivilege',
            name='grantor',
        ),
    ]
