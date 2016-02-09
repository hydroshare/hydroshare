# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
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
            ],
        ),
        migrations.CreateModel(
            name='GroupResourcePrivilege',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('privilege', models.IntegerField(default=3, editable=False, choices=[(1, b'Owner'), (2, b'Change'), (3, b'View')])),
                ('start', models.DateTimeField(auto_now=True)),
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
            ],
        ),
        migrations.CreateModel(
            name='UserAccess',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
            ],
        ),
        migrations.CreateModel(
            name='UserGroupPrivilege',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('privilege', models.IntegerField(default=3, editable=False, choices=[(1, b'Owner'), (2, b'Change'), (3, b'View')])),
                ('start', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='UserResourcePrivilege',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('privilege', models.IntegerField(default=3, editable=False, choices=[(1, b'Owner'), (2, b'Change'), (3, b'View')])),
                ('start', models.DateTimeField(auto_now=True)),
                ('grantor', models.ForeignKey(related_name='x2urp', editable=False, to=settings.AUTH_USER_MODEL, help_text=b'grantor of privilege')),
            ],
        ),
    ]
