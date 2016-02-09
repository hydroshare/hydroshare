# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('hs_core', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='NetcdfMetaData',
            fields=[
                ('coremetadata_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='hs_core.CoreMetaData')),
            ],
            bases=('hs_core.coremetadata',),
        ),
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
        ),
        migrations.CreateModel(
            name='Variable',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('name', models.CharField(max_length=100)),
                ('unit', models.CharField(max_length=100)),
                ('type', models.CharField(max_length=100, choices=[(b'Char', b'Char'), (b'Byte', b'Byte'), (b'Short', b'Short'), (b'Int', b'Int'), (b'Float', b'Float'), (b'Double', b'Double'), (b'Int64', b'Int64'), (b'Unsigned Byte', b'Unsigned Byte'), (b'Unsigned Short', b'Unsigned Short'), (b'Unsigned Int', b'Unsigned Int'), (b'Unsigned Int64', b'Unsigned Int64'), (b'String', b'String'), (b'User Defined Type', b'User Defined Type'), (b'Unknown', b'Unknown')])),
                ('shape', models.CharField(max_length=100)),
                ('descriptive_name', models.CharField(max_length=100, null=True, verbose_name=b'long name', blank=True)),
                ('method', models.TextField(null=True, verbose_name=b'comment', blank=True)),
                ('missing_value', models.CharField(max_length=100, null=True, blank=True)),
                ('content_type', models.ForeignKey(related_name='hs_app_netcdf_variable_related', to='contenttypes.ContentType')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='NetcdfResource',
            fields=[
            ],
            options={
                'ordering': ('_order',),
                'verbose_name': 'Multidimensional (NetCDF)',
                'proxy': True,
            },
            bases=('hs_core.baseresource',),
        ),
        migrations.AlterUniqueTogether(
            name='originalcoverage',
            unique_together=set([('content_type', 'object_id')]),
        ),
    ]
