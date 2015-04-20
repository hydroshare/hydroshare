# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0001_initial'),
        ('hs_app_netCDF', '0002_auto_20150310_1927'),
    ]

    operations = [
        migrations.CreateModel(
            name='OriginalCoverage',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('_value', models.CharField(max_length=1024, null=True)),
                ('projection_string_type', models.CharField(max_length=20, null=True, choices=[(b'', b'---------'), (b'EPSG Code', b'EPSG Code'), (b'OGC WKT Projection', b'OGC WKT Projection'), (b'Proj4 String', b'Proj4 String')])),
                ('projection_string_text', models.TextField(null=True, blank=True)),
                ('content_type', models.ForeignKey(related_name='hs_app_netcdf_originalcoverage_related', to='contenttypes.ContentType')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='originalcoverage',
            unique_together=set([('content_type', 'object_id')]),
        ),
        migrations.AlterField(
            model_name='variable',
            name='type',
            field=models.CharField(max_length=100, choices=[(b'Char', b'Char'), (b'Byte', b'Byte'), (b'Short', b'Short'), (b'Int', b'Int'), (b'Float', b'Float'), (b'Double', b'Double'), (b'Int64', b'Int64'), (b'Unsigned Byte', b'Unsigned Byte'), (b'Unsigned Short', b'Unsigned Short'), (b'Unsigned Int', b'Unsigned Int'), (b'Unsigned Int64', b'Unsigned Int64'), (b'String', b'String'), (b'User Defined Type', b'User Defined Type'), (b'Unknown', b'Unknown')]),
            preserve_default=True,
        ),
    ]
