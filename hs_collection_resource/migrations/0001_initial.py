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
            name='CollectionItems',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('collection_items', models.ManyToManyField(to='hs_core.BaseResource', null=True, blank=True)),
                ('content_type', models.ForeignKey(related_name='hs_collection_resource_collectionitems_related', to='contenttypes.ContentType')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
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
