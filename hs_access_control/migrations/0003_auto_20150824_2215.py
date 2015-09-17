# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hs_access_control', '0002_auto_20150817_1150'),
    ]

    operations = [
        migrations.AlterField(
            model_name='groupresourceprivilege',
            name='grantor',
            field=models.ForeignKey(related_name='x2grp', editable=False, to='hs_access_control.UserAccess', help_text=b'grantor of privilege'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='groupresourceprivilege',
            name='group',
            field=models.ForeignKey(related_name='g2grp', editable=False, to='hs_access_control.GroupAccess', help_text=b'group to be granted privilege'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='groupresourceprivilege',
            name='resource',
            field=models.ForeignKey(related_name='r2grp', editable=False, to='hs_access_control.ResourceAccess', help_text=b'resource to which privilege applies'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='usergroupprivilege',
            name='grantor',
            field=models.ForeignKey(related_name='x2ugp', editable=False, to='hs_access_control.UserAccess', help_text=b'grantor of privilege'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='usergroupprivilege',
            name='group',
            field=models.ForeignKey(related_name='g2ugp', editable=False, to='hs_access_control.GroupAccess', help_text=b'group to which privilege applies'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='usergroupprivilege',
            name='user',
            field=models.ForeignKey(related_name='u2ugp', editable=False, to='hs_access_control.UserAccess', help_text=b'user to be granted privilege'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='userresourceprivilege',
            name='grantor',
            field=models.ForeignKey(related_name='x2urp', editable=False, to='hs_access_control.UserAccess', help_text=b'grantor of privilege'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='userresourceprivilege',
            name='resource',
            field=models.ForeignKey(related_name='r2urp', editable=False, to='hs_access_control.ResourceAccess', help_text=b'resource to which privilege applies'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='userresourceprivilege',
            name='user',
            field=models.ForeignKey(related_name='u2urp', editable=False, to='hs_access_control.UserAccess', help_text=b'user to be granted privilege'),
            preserve_default=True,
        ),
    ]
