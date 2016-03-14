# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('hs_core', '0019_baseresource_locked_time'),
    ]

    operations = [
        migrations.CreateModel(
            name='Collection',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('content_type', models.ForeignKey(related_name='hs_collection_resource_collection_related', to='contenttypes.ContentType')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='CollectionMetaData',
            fields=[
                ('coremetadata_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='hs_core.CoreMetaData')),
            ],
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
        migrations.AddField(
            model_name='collection',
            name='resources',
            field=models.ManyToManyField(to='hs_core.BaseResource', null=True, blank=True),
        ),
    ]
