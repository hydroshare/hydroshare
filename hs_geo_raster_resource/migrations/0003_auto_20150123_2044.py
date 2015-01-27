# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hs_geo_raster_resource', '0002_rastermetadata_bandcount'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='rastermetadata',
            name='bandCount',
        ),
        migrations.RemoveField(
            model_name='rastermetadata',
            name='cellDataType',
        ),
        migrations.RemoveField(
            model_name='rastermetadata',
            name='cellSizeUnit',
        ),
        migrations.RemoveField(
            model_name='rastermetadata',
            name='cellSizeXValue',
        ),
        migrations.RemoveField(
            model_name='rastermetadata',
            name='cellSizeYValue',
        ),
        migrations.RemoveField(
            model_name='rastermetadata',
            name='columns',
        ),
        migrations.RemoveField(
            model_name='rastermetadata',
            name='noDataValue',
        ),
        migrations.RemoveField(
            model_name='rastermetadata',
            name='rows',
        ),
        migrations.AddField(
            model_name='rasterresource',
            name='bandCount',
            field=models.IntegerField(null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='rasterresource',
            name='cellDataType',
            field=models.CharField(max_length=50, null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='rasterresource',
            name='cellSizeUnit',
            field=models.CharField(max_length=50, null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='rasterresource',
            name='cellSizeXValue',
            field=models.FloatField(null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='rasterresource',
            name='cellSizeYValue',
            field=models.FloatField(null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='rasterresource',
            name='columns',
            field=models.IntegerField(null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='rasterresource',
            name='noDataValue',
            field=models.FloatField(null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='rasterresource',
            name='rows',
            field=models.IntegerField(null=True),
            preserve_default=True,
        ),
    ]
