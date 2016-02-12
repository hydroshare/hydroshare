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
            name='BandInformation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('name', models.CharField(max_length=500, null=True)),
                ('variableName', models.TextField(max_length=100, null=True)),
                ('variableUnit', models.CharField(max_length=50, null=True)),
                ('method', models.TextField(null=True, blank=True)),
                ('comment', models.TextField(null=True, blank=True)),
                ('content_type', models.ForeignKey(related_name='hs_geo_raster_resource_bandinformation_related', to='contenttypes.ContentType')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='CellInformation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('name', models.CharField(max_length=500, null=True)),
                ('rows', models.IntegerField(null=True)),
                ('columns', models.IntegerField(null=True)),
                ('cellSizeXValue', models.FloatField(null=True)),
                ('cellSizeYValue', models.FloatField(null=True)),
                ('cellDataType', models.CharField(max_length=50, null=True)),
                ('noDataValue', models.FloatField(null=True, blank=True)),
                ('content_type', models.ForeignKey(related_name='hs_geo_raster_resource_cellinformation_related', to='contenttypes.ContentType')),
            ],
        ),
        migrations.CreateModel(
            name='OriginalCoverage',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('_value', models.CharField(max_length=1024, null=True)),
                ('content_type', models.ForeignKey(related_name='hs_geo_raster_resource_originalcoverage_related', to='contenttypes.ContentType')),
            ],
        ),
        migrations.CreateModel(
            name='RasterMetaData',
            fields=[
                ('coremetadata_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='hs_core.CoreMetaData')),
            ],
            bases=('hs_core.coremetadata',),
        ),
        migrations.CreateModel(
            name='RasterResource',
            fields=[
            ],
            options={
                'ordering': ('_order',),
                'verbose_name': 'Geographic Raster',
                'proxy': True,
            },
            bases=('hs_core.baseresource',),
        ),
        migrations.AlterUniqueTogether(
            name='originalcoverage',
            unique_together=set([('content_type', 'object_id')]),
        ),
        migrations.AlterUniqueTogether(
            name='cellinformation',
            unique_together=set([('content_type', 'object_id')]),
        ),
    ]
