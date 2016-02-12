# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('hs_core', '__first__'),
    ]

    operations = [
        migrations.CreateModel(
            name='RequestUrlBase',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('value', models.CharField(max_length=1024, null=True)),
                ('content_type', models.ForeignKey(related_name='hs_tools_resource_requesturlbase_related', to='contenttypes.ContentType')),
            ],
        ),
        migrations.CreateModel(
            name='SupportedResTypeChoices',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('description', models.CharField(max_length=128)),
            ],
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
        ),
        migrations.CreateModel(
            name='ToolIcon',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('url', models.CharField(max_length=1024, null=True, blank=True)),
                ('content_type', models.ForeignKey(related_name='hs_tools_resource_toolicon_related', to='contenttypes.ContentType')),
            ],
        ),
        migrations.CreateModel(
            name='ToolMetaData',
            fields=[
                ('coremetadata_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='hs_core.CoreMetaData')),
            ],
            bases=('hs_core.coremetadata',),
        ),
        migrations.CreateModel(
            name='ToolVersion',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('value', models.CharField(max_length=128, blank=True)),
                ('content_type', models.ForeignKey(related_name='hs_tools_resource_toolversion_related', to='contenttypes.ContentType')),
            ],
        ),
        migrations.CreateModel(
            name='ToolResource',
            fields=[
            ],
            options={
                'ordering': ('_order',),
                'verbose_name': 'Web App Resource',
                'proxy': True,
            },
            bases=('hs_core.baseresource',),
        ),
        migrations.AlterUniqueTogether(
            name='toolversion',
            unique_together=set([('content_type', 'object_id')]),
        ),
        migrations.AlterUniqueTogether(
            name='toolicon',
            unique_together=set([('content_type', 'object_id')]),
        ),
        migrations.AlterUniqueTogether(
            name='requesturlbase',
            unique_together=set([('content_type', 'object_id')]),
        ),
    ]
