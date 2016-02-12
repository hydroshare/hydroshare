# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('auth', '0006_require_contenttypes_0002'),
        ('hs_core', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='GroupAccess',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('active', models.BooleanField(default=True, help_text=b'whether group is currently active', editable=False)),
                ('discoverable', models.BooleanField(default=True, help_text=b'whether group description is discoverable by everyone', editable=False)),
                ('public', models.BooleanField(default=True, help_text=b'whether group members can be listed by everyone', editable=False)),
                ('shareable', models.BooleanField(default=True, help_text=b'whether group can be shared by non-owners', editable=False)),
                ('group', models.OneToOneField(related_query_name=b'gaccess', related_name='gaccess', editable=False, to='auth.Group', help_text=b'group object that this object protects')),
            ],
        ),
        migrations.CreateModel(
            name='GroupResourcePrivilege',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('privilege', models.IntegerField(default=3, editable=False, choices=[(1, b'Owner'), (2, b'Change'), (3, b'View')])),
                ('start', models.DateTimeField(auto_now=True)),
                ('grantor', models.ForeignKey(related_name='x2grp', editable=False, to=settings.AUTH_USER_MODEL, help_text=b'grantor of privilege')),
                ('group', models.ForeignKey(related_name='g2grp', editable=False, to='auth.Group', help_text=b'group to be granted privilege')),
                ('resource', models.ForeignKey(related_name='r2grp', editable=False, to='hs_core.BaseResource', help_text=b'resource to which privilege applies')),
            ],
        ),
        migrations.CreateModel(
            name='ResourceAccess',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('active', models.BooleanField(default=True, help_text=b'whether resource is currently active')),
                ('discoverable', models.BooleanField(default=False, help_text=b'whether resource is discoverable by everyone')),
                ('public', models.BooleanField(default=False, help_text=b'whether resource data can be viewed by everyone')),
                ('shareable', models.BooleanField(default=True, help_text=b'whether resource can be shared by non-owners')),
                ('published', models.BooleanField(default=False, help_text=b'whether resource has been published')),
                ('immutable', models.BooleanField(default=False, help_text=b'whether to prevent all changes to the resource')),
                ('resource', models.OneToOneField(related_query_name=b'raccess', related_name='raccess', editable=False, to='hs_core.BaseResource')),
            ],
        ),
        migrations.CreateModel(
            name='UserAccess',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('user', models.OneToOneField(related_query_name=b'uaccess', related_name='uaccess', editable=False, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='UserGroupPrivilege',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('privilege', models.IntegerField(default=3, editable=False, choices=[(1, b'Owner'), (2, b'Change'), (3, b'View')])),
                ('start', models.DateTimeField(auto_now=True)),
                ('grantor', models.ForeignKey(related_name='x2ugp', editable=False, to=settings.AUTH_USER_MODEL, help_text=b'grantor of privilege')),
                ('group', models.ForeignKey(related_name='g2ugp', editable=False, to='auth.Group', help_text=b'group to which privilege applies')),
                ('user', models.ForeignKey(related_name='u2ugp', editable=False, to=settings.AUTH_USER_MODEL, help_text=b'user to be granted privilege')),
            ],
        ),
        migrations.CreateModel(
            name='UserResourcePrivilege',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('privilege', models.IntegerField(default=3, editable=False, choices=[(1, b'Owner'), (2, b'Change'), (3, b'View')])),
                ('start', models.DateTimeField(auto_now=True)),
                ('grantor', models.ForeignKey(related_name='x2urp', editable=False, to=settings.AUTH_USER_MODEL, help_text=b'grantor of privilege')),
                ('resource', models.ForeignKey(related_name='r2urp', editable=False, to='hs_core.BaseResource', help_text=b'resource to which privilege applies')),
                ('user', models.ForeignKey(related_name='u2urp', editable=False, to=settings.AUTH_USER_MODEL, help_text=b'user to be granted privilege')),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='userresourceprivilege',
            unique_together=set([('user', 'resource', 'grantor')]),
        ),
        migrations.AlterUniqueTogether(
            name='usergroupprivilege',
            unique_together=set([('user', 'group', 'grantor')]),
        ),
        migrations.AlterUniqueTogether(
            name='groupresourceprivilege',
            unique_together=set([('group', 'resource', 'grantor')]),
        ),
    ]
