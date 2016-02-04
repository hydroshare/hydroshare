# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hs_access_control', '0012_auto_disallow_nulls'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='groupresourceprivilege',
            unique_together=set([('group', 'resource', 'grantor')]),
        ),
        migrations.AlterUniqueTogether(
            name='usergroupprivilege',
            unique_together=set([('user', 'group', 'grantor')]),
        ),
        migrations.AlterUniqueTogether(
            name='userresourceprivilege',
            unique_together=set([('user', 'resource', 'grantor')]),
        ),
    ]
