# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hs_access_control', '0015_manual_remove_redundant_privileges'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='groupresourceprivilege',
            unique_together=set([('group', 'resource')]),
        ),
        migrations.AlterUniqueTogether(
            name='usergroupprivilege',
            unique_together=set([('user', 'group')]),
        ),
        migrations.AlterUniqueTogether(
            name='userresourceprivilege',
            unique_together=set([('user', 'resource')]),
        ),
    ]
