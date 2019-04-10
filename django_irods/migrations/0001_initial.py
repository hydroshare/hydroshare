# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='RodsEnvironment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('host', models.CharField(max_length=255, verbose_name=b'Hostname')),
                ('port', models.IntegerField()),
                ('def_res', models.CharField(max_length=255, verbose_name=b'Default resource')),
                ('home_coll', models.CharField(max_length=255, verbose_name=b'Home collection')),
                ('cwd', models.TextField(verbose_name=b'Working directory')),
                ('username', models.CharField(max_length=255)),
                ('zone', models.TextField()),
                ('auth', models.TextField(verbose_name=b'Password')),
                ('owner', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'iRODS Environment',
            },
            bases=(models.Model,),
        ),
    ]
