# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0001_initial'),
        ('hs_geo_raster_resource', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='CellInformation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('name', models.CharField(max_length=50, null=True)),
                ('rows', models.IntegerField(null=True)),
                ('columns', models.IntegerField(null=True)),
                ('cellSizeXValue', models.FloatField(null=True)),
                ('cellSizeYValue', models.FloatField(null=True)),
                ('cellSizeUnit', models.CharField(max_length=50, null=True)),
                ('cellDataType', models.CharField(max_length=50, null=True)),
                ('noDataValue', models.FloatField(null=True)),
                ('content_type', models.ForeignKey(related_name='hs_geo_raster_resource_cellinformation_related', to='contenttypes.ContentType')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.RemoveField(
            model_name='rasterresource',
            name='bandCount',
        ),
        migrations.RemoveField(
            model_name='rasterresource',
            name='cellDataType',
        ),
        migrations.RemoveField(
            model_name='rasterresource',
            name='cellSizeUnit',
        ),
        migrations.RemoveField(
            model_name='rasterresource',
            name='cellSizeXValue',
        ),
        migrations.RemoveField(
            model_name='rasterresource',
            name='cellSizeYValue',
        ),
        migrations.RemoveField(
            model_name='rasterresource',
            name='columns',
        ),
        migrations.RemoveField(
            model_name='rasterresource',
            name='noDataValue',
        ),
        migrations.RemoveField(
            model_name='rasterresource',
            name='rows',
        ),
    ]
