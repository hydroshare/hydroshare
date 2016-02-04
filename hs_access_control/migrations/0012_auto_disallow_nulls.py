# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('hs_access_control', '0011_auto_rename_new_fields_to_original_names'),
    ]

    operations = [
        migrations.AlterField(
            model_name='groupaccess',
            name='group',
            field=models.OneToOneField(related_query_name=b'gaccess', related_name='gaccess', editable=False, to='auth.Group', help_text=b'group object that this object protects'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='groupresourceprivilege',
            name='grantor',
            field=models.ForeignKey(related_name='x2grp', editable=False, to=settings.AUTH_USER_MODEL, help_text=b'grantor of privilege'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='groupresourceprivilege',
            name='group',
            field=models.ForeignKey(related_name='g2grp', editable=False, to='auth.Group', help_text=b'group to be granted privilege'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='groupresourceprivilege',
            name='resource',
            field=models.ForeignKey(related_name='r2grp', editable=False, to='hs_core.BaseResource', help_text=b'resource to which privilege applies'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='resourceaccess',
            name='resource',
            field=models.OneToOneField(related_query_name=b'raccess', related_name='raccess', editable=False, to='hs_core.BaseResource'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='useraccess',
            name='user',
            field=models.OneToOneField(related_query_name=b'uaccess', related_name='uaccess', editable=False, to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='usergroupprivilege',
            name='grantor',
            field=models.ForeignKey(related_name='x2ugp', editable=False, to=settings.AUTH_USER_MODEL, help_text=b'grantor of privilege'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='usergroupprivilege',
            name='group',
            field=models.ForeignKey(related_name='g2ugp', editable=False, to='auth.Group', help_text=b'group to which privilege applies'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='usergroupprivilege',
            name='user',
            field=models.ForeignKey(related_name='u2ugp', editable=False, to=settings.AUTH_USER_MODEL, help_text=b'user to be granted privilege'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='userresourceprivilege',
            name='grantor',
            field=models.ForeignKey(related_name='x2urp', editable=False, to=settings.AUTH_USER_MODEL, help_text=b'grantor of privilege'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='userresourceprivilege',
            name='resource',
            field=models.ForeignKey(related_name='r2urp', editable=False, to='hs_core.BaseResource', help_text=b'resource to which privilege applies'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='userresourceprivilege',
            name='user',
            field=models.ForeignKey(related_name='u2urp', editable=False, to=settings.AUTH_USER_MODEL, help_text=b'user to be granted privilege'),
            preserve_default=True,
        ),
    ]
