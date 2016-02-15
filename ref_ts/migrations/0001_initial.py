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
            name='DataSource',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('code', models.CharField(default=b'', max_length=500, blank=True)),
                ('content_type', models.ForeignKey(related_name='ref_ts_datasource_related', to='contenttypes.ContentType')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Method',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('code', models.CharField(default=b'', max_length=500, blank=True)),
                ('description', models.TextField(default=b'', blank=True)),
                ('content_type', models.ForeignKey(related_name='ref_ts_method_related', to='contenttypes.ContentType')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='QualityControlLevel',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('code', models.CharField(default=b'', max_length=500, blank=True)),
                ('definition', models.CharField(default=b'', max_length=500, blank=True)),
                ('content_type', models.ForeignKey(related_name='ref_ts_qualitycontrollevel_related', to='contenttypes.ContentType')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ReferenceURL',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('value', models.CharField(max_length=500)),
                ('type', models.CharField(max_length=4)),
                ('content_type', models.ForeignKey(related_name='ref_ts_referenceurl_related', to='contenttypes.ContentType')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='RefTSMetadata',
            fields=[
                ('coremetadata_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='hs_core.CoreMetaData')),
            ],
            bases=('hs_core.coremetadata',),
        ),
        migrations.CreateModel(
            name='Site',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('name', models.CharField(default=b'', max_length=500, blank=True)),
                ('code', models.CharField(default=b'', max_length=500, blank=True)),
                ('net_work', models.CharField(default=b'', max_length=500, blank=True)),
                ('latitude', models.DecimalField(null=True, max_digits=9, decimal_places=6, blank=True)),
                ('longitude', models.DecimalField(null=True, max_digits=9, decimal_places=6, blank=True)),
                ('content_type', models.ForeignKey(related_name='ref_ts_site_related', to='contenttypes.ContentType')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Variable',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('name', models.CharField(default=b'', max_length=500, blank=True)),
                ('code', models.CharField(default=b'', max_length=500, blank=True)),
                ('data_type', models.CharField(default=b'', max_length=500, blank=True)),
                ('sample_medium', models.CharField(default=b'', max_length=500, blank=True)),
                ('content_type', models.ForeignKey(related_name='ref_ts_variable_related', to='contenttypes.ContentType')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='RefTimeSeriesResource',
            fields=[
            ],
            options={
                'ordering': ('_order',),
                'verbose_name': 'HIS Referenced Time Series',
                'proxy': True,
            },
            bases=('hs_core.baseresource',),
        ),
    ]
