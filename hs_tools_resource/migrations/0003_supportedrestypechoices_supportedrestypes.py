# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0001_initial'),
        ('hs_tools_resource', '0002_auto_20150708_2304'),
    ]

    operations = [
        migrations.CreateModel(
            name='SupportedResTypeChoices',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('description', models.CharField(max_length=300)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='SupportedResTypes',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('content_type', models.ForeignKey(related_name='hs_tools_resource_supportedrestypes_related', to='contenttypes.ContentType')),
                ('supported_res_types', models.ManyToManyField(to='hs_tools_resource.SupportedResTypeChoices', null=True, blank=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
    ]
