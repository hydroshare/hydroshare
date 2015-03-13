# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0001_initial'),
        ('hs_geo_raster_resource', '0002_auto_20150310_1927'),
    ]

    operations = [
        migrations.CreateModel(
            name='OriginalCoverage',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('_value', models.CharField(max_length=1024, null=True)),
                ('content_type', models.ForeignKey(related_name='hs_geo_raster_resource_originalcoverage_related', to='contenttypes.ContentType')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='originalcoverage',
            unique_together=set([('content_type', 'object_id')]),
        ),
    ]
