# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hs_core', '0006_auto_20150917_1515'),
        ('contenttypes', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='FieldInformation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('fieldName', models.CharField(max_length=128)),
                ('fieldType', models.CharField(max_length=128)),
                ('fieldTypeCode', models.CharField(max_length=50, null=True, blank=True)),
                ('fieldWidth', models.IntegerField(null=True, blank=True)),
                ('fieldPrecision', models.IntegerField(null=True, blank=True)),
                ('content_type', models.ForeignKey(related_name='hs_geographic_feature_resource_fieldinformation_related', to='contenttypes.ContentType')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='GeographicFeatureMetaData',
            fields=[
                ('coremetadata_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='hs_core.CoreMetaData')),
            ],
            options={
            },
            bases=('hs_core.coremetadata',),
        ),
        migrations.CreateModel(
            name='GeometryInformation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('featureCount', models.IntegerField(default=0)),
                ('geometryType', models.CharField(max_length=128)),
                ('content_type', models.ForeignKey(related_name='hs_geographic_feature_resource_geometryinformation_related', to='contenttypes.ContentType')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='OriginalCoverage',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('northlimit', models.FloatField()),
                ('southlimit', models.FloatField()),
                ('westlimit', models.FloatField()),
                ('eastlimit', models.FloatField()),
                ('projection_string', models.TextField(null=True, blank=True)),
                ('projection_name', models.TextField(max_length=256, null=True, blank=True)),
                ('datum', models.TextField(max_length=256, null=True, blank=True)),
                ('unit', models.TextField(max_length=256, null=True, blank=True)),
                ('content_type', models.ForeignKey(related_name='hs_geographic_feature_resource_originalcoverage_related', to='contenttypes.ContentType')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='OriginalFileInfo',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('fileType', models.TextField(default=None, max_length=128, choices=[(None, 'Unknown'), ('SHP', 'ESRI Shapefiles'), ('ZSHP', 'Zipped ESRI Shapefiles'), ('KML', 'KML'), ('KMZ', 'KMZ'), ('GML', 'GML'), ('SQLITE', 'SQLite')])),
                ('baseFilename', models.TextField(max_length=256)),
                ('fileCount', models.IntegerField(default=0)),
                ('filenameString', models.TextField(null=True, blank=True)),
                ('content_type', models.ForeignKey(related_name='hs_geographic_feature_resource_originalfileinfo_related', to='contenttypes.ContentType')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='originalfileinfo',
            unique_together=set([('content_type', 'object_id')]),
        ),
        migrations.AlterUniqueTogether(
            name='originalcoverage',
            unique_together=set([('content_type', 'object_id')]),
        ),
        migrations.AlterUniqueTogether(
            name='geometryinformation',
            unique_together=set([('content_type', 'object_id')]),
        ),
        migrations.CreateModel(
            name='GeographicFeatureResource',
            fields=[
            ],
            options={
                'ordering': ('_order',),
                'verbose_name': 'Geographic Feature (ESRI Shapefiles)',
                'proxy': True,
            },
            bases=('hs_core.baseresource',),
        ),
    ]
