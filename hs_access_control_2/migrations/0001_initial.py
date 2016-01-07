# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('hs_core', '0014_auto_20151123_1451'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('auth', '0001_initial'),
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
                ('group', models.OneToOneField(related_query_name=b'gaccess2', related_name='gaccess2', null=True, editable=False, to='auth.Group', help_text=b'group object that this object protects')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='GroupResourcePrivilege',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('privilege', models.IntegerField(default=3, editable=False, choices=[(1, b'Owner'), (2, b'Change'), (3, b'View')])),
                ('start', models.DateTimeField(auto_now=True)),
                ('grantor', models.ForeignKey(related_name='x2grp2', editable=False, to=settings.AUTH_USER_MODEL, help_text=b'grantor of privilege')),
                ('group', models.ForeignKey(related_name='g2grp2', editable=False, to='auth.Group', help_text=b'group to be granted privilege')),
                ('resource', models.ForeignKey(related_name='r2grp2', editable=False, to='hs_core.BaseResource', help_text=b'resource to which privilege applies')),
            ],
            options={
            },
            bases=(models.Model,),
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
                ('resource', models.OneToOneField(related_query_name=b'raccess2', related_name='raccess2', null=True, editable=False, to='hs_core.BaseResource')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='UserAccess',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('user', models.OneToOneField(related_query_name=b'uaccess2', related_name='uaccess2', null=True, editable=False, to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='UserGroupPrivilege',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('privilege', models.IntegerField(default=3, editable=False, choices=[(1, b'Owner'), (2, b'Change'), (3, b'View')])),
                ('start', models.DateTimeField(auto_now=True)),
                ('grantor', models.ForeignKey(related_name='x2ugp2', editable=False, to=settings.AUTH_USER_MODEL, help_text=b'grantor of privilege')),
                ('group', models.ForeignKey(related_name='g2ugp2', editable=False, to='auth.Group', help_text=b'group to which privilege applies')),
                ('user', models.ForeignKey(related_name='u2ugp2', editable=False, to=settings.AUTH_USER_MODEL, help_text=b'user to be granted privilege')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='UserResourcePrivilege',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('privilege', models.IntegerField(default=3, editable=False, choices=[(1, b'Owner'), (2, b'Change'), (3, b'View')])),
                ('start', models.DateTimeField(auto_now=True)),
                ('grantor', models.ForeignKey(related_name='x2urp2', editable=False, to=settings.AUTH_USER_MODEL, help_text=b'grantor of privilege')),
                ('resource', models.ForeignKey(related_name='r2urp2', editable=False, to='hs_core.BaseResource', help_text=b'resource to which privilege applies')),
                ('user', models.ForeignKey(related_name='u2urp2', editable=False, to=settings.AUTH_USER_MODEL, help_text=b'user to be granted privilege')),
            ],
            options={
            },
            bases=(models.Model,),
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
