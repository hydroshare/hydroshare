# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.contrib.postgres.fields.hstore


class Migration(migrations.Migration):

    dependencies = [
        ('hs_file_types', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='BaseMetaDataElement',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('element_type', models.CharField(default=b'Generic', max_length=100)),
                ('data', django.contrib.postgres.fields.hstore.HStoreField(default={})),
            ],
        ),
        migrations.CreateModel(
            name='NetCDFFileMetaData',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('extra_metadata', django.contrib.postgres.fields.hstore.HStoreField(default={})),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='NetCDFLogicalFile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('dataset_name', models.CharField(max_length=255, null=True, blank=True)),
                ('metadata', models.OneToOneField(related_name='logical_file', to='hs_file_types.NetCDFFileMetaData')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='basemetadataelement',
            name='metadata',
            field=models.ForeignKey(to='hs_file_types.NetCDFFileMetaData'),
        ),
        migrations.CreateModel(
            name='OriginalCoverage',
            fields=[
            ],
            options={
                'verbose_name': 'Original Coverage',
                'proxy': True,
            },
            bases=('hs_file_types.basemetadataelement',),
        ),
    ]
