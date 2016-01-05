# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hs_core', '0014_auto_20151123_1451'),
        ('contenttypes', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='CollectionMetaData',
            fields=[
                ('coremetadata_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='hs_core.CoreMetaData')),
            ],
            options={
            },
            bases=('hs_core.coremetadata',),
        ),
        migrations.CreateModel(
            name='RequestUrlBase',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('value', models.CharField(max_length=1024, null=True)),
                ('resShortID', models.CharField(default=b'UNKNOWN', max_length=128)),
                ('content_type', models.ForeignKey(related_name='hs_collection_resource_requesturlbase_related', to='contenttypes.ContentType')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='SupportedResTypeChoices',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('description', models.CharField(max_length=128)),
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
                ('content_type', models.ForeignKey(related_name='hs_collection_resource_supportedrestypes_related', to='contenttypes.ContentType')),
                ('supported_res_types', models.ManyToManyField(to='hs_core.BaseResource', null=True, blank=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ToolVersion',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('value', models.CharField(default=b'1.0', max_length=128)),
                ('content_type', models.ForeignKey(related_name='hs_collection_resource_toolversion_related', to='contenttypes.ContentType')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='toolversion',
            unique_together=set([('content_type', 'object_id')]),
        ),
        migrations.AlterUniqueTogether(
            name='requesturlbase',
            unique_together=set([('content_type', 'object_id')]),
        ),
        migrations.CreateModel(
            name='CollectionResource',
            fields=[
            ],
            options={
                'ordering': ('_order',),
                'verbose_name': 'Collection Resource',
                'proxy': True,
            },
            bases=('hs_core.baseresource',),
        ),
    ]
