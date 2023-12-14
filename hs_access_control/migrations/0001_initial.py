# -*- coding: utf-8 -*-


from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('hs_core', '0004_auto_20150721_1125'),
    ]

    operations = [
        migrations.CreateModel(
            name='GroupAccess',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('active', models.BooleanField(default=True, help_text='whether group is currently active', editable=False)),
                ('discoverable', models.BooleanField(default=True, help_text='whether group description is discoverable by everyone', editable=False)),
                ('public', models.BooleanField(default=True, help_text='whether group members can be listed by everyone', editable=False)),
                ('shareable', models.BooleanField(default=True, help_text='whether group can be shared by non-owners', editable=False)),
                ('group', models.OneToOneField(related_query_name='gaccess', related_name='gaccess', null=True, editable=False, on_delete=models.CASCADE, to='auth.Group', help_text='group object that this object protects')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='GroupResourcePrivilege',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('privilege', models.IntegerField(default=3, editable=False, choices=[(1, 'Owner'), (2, 'Change'), (3, 'View')])),
                ('start', models.DateTimeField(auto_now=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ResourceAccess',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('active', models.BooleanField(default=True, help_text='whether resource is currently active')),
                ('discoverable', models.BooleanField(default=False, help_text='whether resource is discoverable by everyone')),
                ('public', models.BooleanField(default=False, help_text='whether resource data can be viewed by everyone')),
                ('shareable', models.BooleanField(default=True, help_text='whether resource can be shared by non-owners')),
                ('published', models.BooleanField(default=False, help_text='whether resource has been published')),
                ('immutable', models.BooleanField(default=False, help_text='whether to prevent all changes to the resource')),
                ('holding_groups', models.ManyToManyField(help_text='groups that hold this resource', related_name='group2resource', editable=False, through='hs_access_control.GroupResourcePrivilege', to='hs_access_control.GroupAccess')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='UserAccess',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('active', models.BooleanField(default=True, help_text='whether user is currently capable of action', editable=False)),
                ('admin', models.BooleanField(default=False, help_text='whether user is an administrator', editable=False)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='UserGroupPrivilege',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('privilege', models.IntegerField(default=3, editable=False, choices=[(1, 'Owner'), (2, 'Change'), (3, 'View')])),
                ('start', models.DateTimeField(auto_now=True)),
                ('grantor', models.ForeignKey(related_name='x2ugp', editable=False, on_delete=models.CASCADE, to='hs_access_control.UserAccess', help_text='grantor of privilege', null=True)),
                ('group', models.ForeignKey(related_name='g2ugp', editable=False, on_delete=models.CASCADE, to='hs_access_control.GroupAccess', help_text='group to which privilege applies', null=True)),
                ('user', models.ForeignKey(related_name='u2ugp', editable=False, on_delete=models.CASCADE, to='hs_access_control.UserAccess', help_text='user to be granted privilege', null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='UserResourcePrivilege',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('privilege', models.IntegerField(default=3, editable=False, choices=[(1, 'Owner'), (2, 'Change'), (3, 'View')])),
                ('start', models.DateTimeField(auto_now=True)),
                ('grantor', models.ForeignKey(related_name='x2urp', editable=False, on_delete=models.CASCADE, to='hs_access_control.UserAccess', help_text='grantor of privilege', null=True)),
                ('resource', models.ForeignKey(related_name='r2urp', editable=False, on_delete=models.CASCADE, to='hs_access_control.ResourceAccess', help_text='resource to which privilege applies', null=True)),
                ('user', models.ForeignKey(related_name='u2urp', editable=False, on_delete=models.CASCADE, to='hs_access_control.UserAccess', help_text='user to be granted privilege', null=True)),
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
        migrations.AddField(
            model_name='useraccess',
            name='held_groups',
            field=models.ManyToManyField(help_text='groups held by this user', related_name='group2user', editable=False, through='hs_access_control.UserGroupPrivilege', to='hs_access_control.GroupAccess'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='useraccess',
            name='held_resources',
            field=models.ManyToManyField(help_text='resources held by this user', related_name='resource2user', editable=False, through='hs_access_control.UserResourcePrivilege', to='hs_access_control.ResourceAccess'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='useraccess',
            name='user',
            field=models.OneToOneField(related_query_name='uaccess', related_name='uaccess', null=True, editable=False, on_delete=models.CASCADE, to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='resourceaccess',
            name='holding_users',
            field=models.ManyToManyField(help_text='users who hold this resource', related_name='user2resource', editable=False, through='hs_access_control.UserResourcePrivilege', to='hs_access_control.UserAccess'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='resourceaccess',
            name='resource',
            field=models.OneToOneField(related_query_name='raccess', related_name='raccess', null=True, editable=False, on_delete=models.CASCADE, to='hs_core.BaseResource'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='groupresourceprivilege',
            name='grantor',
            field=models.ForeignKey(related_name='x2grp', editable=False, on_delete=models.CASCADE, to='hs_access_control.UserAccess', help_text='grantor of privilege', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='groupresourceprivilege',
            name='group',
            field=models.ForeignKey(related_name='g2grp', editable=False, on_delete=models.CASCADE, to='hs_access_control.GroupAccess', help_text='group to be granted privilege', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='groupresourceprivilege',
            name='resource',
            field=models.ForeignKey(related_name='r2grp', editable=False, on_delete=models.CASCADE, to='hs_access_control.ResourceAccess', help_text='resource to which privilege applies', null=True),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='groupresourceprivilege',
            unique_together=set([('group', 'resource', 'grantor')]),
        ),
        migrations.AddField(
            model_name='groupaccess',
            name='held_resources',
            field=models.ManyToManyField(help_text='resources held by the group', related_name='resource2group', editable=False, through='hs_access_control.GroupResourcePrivilege', to='hs_access_control.ResourceAccess'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='groupaccess',
            name='members',
            field=models.ManyToManyField(help_text='members of the group', related_name='user2group', editable=False, through='hs_access_control.UserGroupPrivilege', to='hs_access_control.UserAccess'),
            preserve_default=True,
        ),
    ]
