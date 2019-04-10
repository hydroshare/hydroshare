# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('auth', '0006_require_contenttypes_0002'),
        ('hs_core', '0029_auto_20161123_1858'),
        ('hs_access_control', '0016_auto_enforce_constraints'),
    ]

    operations = [
        migrations.CreateModel(
            name='GroupResourceProvenance',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('privilege', models.IntegerField(default=3, editable=False, choices=[(1, b'Owner'), (2, b'Change'), (3, b'View')])),
                ('start', models.DateTimeField(auto_now_add=True)),
                ('grantor', models.ForeignKey(related_name='x2grq', editable=False, to=settings.AUTH_USER_MODEL, help_text=b'grantor of privilege')),
                ('group', models.ForeignKey(related_name='g2grq', editable=False, to='auth.Group', help_text=b'group to be granted privilege')),
                ('resource', models.ForeignKey(related_name='r2grq', editable=False, to='hs_core.BaseResource', help_text=b'resource to which privilege applies')),
            ],
        ),
        migrations.CreateModel(
            name='UserGroupProvenance',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('privilege', models.IntegerField(default=3, editable=False, choices=[(1, b'Owner'), (2, b'Change'), (3, b'View')])),
                ('start', models.DateTimeField(auto_now_add=True)),
                ('grantor', models.ForeignKey(related_name='x2ugq', editable=False, to=settings.AUTH_USER_MODEL, help_text=b'grantor of privilege')),
                ('group', models.ForeignKey(related_name='g2ugq', editable=False, to='auth.Group', help_text=b'group to which privilege applies')),
                ('user', models.ForeignKey(related_name='u2ugq', editable=False, to=settings.AUTH_USER_MODEL, help_text=b'user to be granted privilege')),
            ],
        ),
        migrations.CreateModel(
            name='UserResourceProvenance',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('privilege', models.IntegerField(default=3, editable=False, choices=[(1, b'Owner'), (2, b'Change'), (3, b'View')])),
                ('start', models.DateTimeField(auto_now_add=True)),
                ('grantor', models.ForeignKey(related_name='x2urq', editable=False, to=settings.AUTH_USER_MODEL, help_text=b'grantor of privilege')),
                ('resource', models.ForeignKey(related_name='r2urq', editable=False, to='hs_core.BaseResource', help_text=b'resource to which privilege applies')),
                ('user', models.ForeignKey(related_name='u2urq', editable=False, to=settings.AUTH_USER_MODEL, help_text=b'user to be granted privilege')),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='userresourceprovenance',
            unique_together=set([('user', 'resource', 'start')]),
        ),
        migrations.AlterUniqueTogether(
            name='usergroupprovenance',
            unique_together=set([('user', 'group', 'start')]),
        ),
        migrations.AlterUniqueTogether(
            name='groupresourceprovenance',
            unique_together=set([('group', 'resource', 'start')]),
        ),
    ]
