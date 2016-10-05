# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('hs_geo_raster_resource', 'custom_migration_for_raster_meta_update_20160512'),
    ]

    operations = [
        migrations.CreateModel(
            name='OGCWebServices',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('layerName', models.CharField(max_length=500, null=True)),
                ('wmsEndpoint', models.CharField(max_length=500, null=True)),
                ('wcsEndpoint', models.CharField(max_length=500, null=True)),
                ('content_type', models.ForeignKey(related_name='hs_geo_raster_resource_ogcwebservices_related', to='contenttypes.ContentType')),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='ogcwebservices',
            unique_together=set([('content_type', 'object_id')]),
        ),
    ]
