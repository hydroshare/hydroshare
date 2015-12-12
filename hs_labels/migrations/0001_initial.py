# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('hs_core', '0014_auto_20151123_1451'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ResourceLabels',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('resource', models.OneToOneField(related_query_name=b'rlabels', related_name='rlabels', null=True, editable=False, to='hs_core.BaseResource')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='UserLabels',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('user', models.OneToOneField(related_query_name=b'ulabels', related_name='ulabels', null=True, editable=False, to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='UserResourceFlags',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('kind', models.IntegerField(default=1, editable=False, choices=[(1, b'Favorite'), (2, b'Mine')])),
                ('start', models.DateTimeField(auto_now=True)),
                ('resource', models.ForeignKey(related_name='r2urf', editable=False, to='hs_core.BaseResource', help_text=b'resource to which a flag applies')),
                ('user', models.ForeignKey(related_name='u2urf', editable=False, to=settings.AUTH_USER_MODEL, help_text=b'user assigning a flag')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='UserResourceLabels',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('start', models.DateTimeField(auto_now=True)),
                ('label', models.TextField()),
                ('resource', models.ForeignKey(related_name='r2url', editable=False, to='hs_core.BaseResource', help_text=b'resource to which a label applies')),
                ('user', models.ForeignKey(related_name='u2url', editable=False, to=settings.AUTH_USER_MODEL, help_text=b'user assigning a label')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='UserStoredLabels',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('label', models.TextField(help_text=b'label to be stored by user')),
                ('user', models.ForeignKey(related_name='ul2usl', to=settings.AUTH_USER_MODEL, help_text=b'user who stored the label', null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
