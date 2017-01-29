# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.contrib.postgres.fields
import django.contrib.postgres.fields.hstore


class Migration(migrations.Migration):

    dependencies = [
        ('hs_file_types', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='BaseFileMetaData',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('file_metadata_type', models.CharField(default=b'Generic', max_length=100)),
                ('extra_metadata', django.contrib.postgres.fields.hstore.HStoreField(default={})),
                ('keywords', django.contrib.postgres.fields.ArrayField(default=[], base_field=models.CharField(max_length=100, null=True, blank=True), size=None)),
            ],
        ),
        migrations.CreateModel(
            name='BaseMetaDataElement',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('element_type', models.CharField(default=b'Generic', max_length=100)),
                ('data', django.contrib.postgres.fields.hstore.HStoreField(default={})),
                ('metadata', models.ForeignKey(to='hs_file_types.BaseFileMetaData')),
            ],
        ),
        migrations.CreateModel(
            name='NetCDFLogicalFile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('dataset_name', models.CharField(max_length=255, null=True, blank=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Coverage',
            fields=[
            ],
            options={
                'verbose_name': 'Coverage',
                'proxy': True,
            },
            bases=('hs_file_types.basemetadataelement',),
        ),
        migrations.CreateModel(
            name='NetCDFFileMetaData',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('hs_file_types.basefilemetadata',),
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
        migrations.CreateModel(
            name='Variable',
            fields=[
            ],
            options={
                'verbose_name': 'Variable',
                'proxy': True,
            },
            bases=('hs_file_types.basemetadataelement',),
        ),
        migrations.AddField(
            model_name='netcdflogicalfile',
            name='metadata',
            field=models.OneToOneField(related_name='logical_file', to='hs_file_types.NetCDFFileMetaData'),
        ),
    ]
