# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings
import hs_core.models


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0001_initial'),
        ('pages', '__first__'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('contenttypes', '0001_initial'),
        ('hs_core', '0001_initial'),
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
            bases=(models.Model,),
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
                ('cellSizeUnit', models.CharField(max_length=50, null=True)),
                ('cellDataType', models.CharField(max_length=50, null=True)),
                ('noDataValue', models.FloatField(null=True)),
                ('content_type', models.ForeignKey(related_name='hs_geo_raster_resource_cellinformation_related', to='contenttypes.ContentType')),
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
                ('_value', models.CharField(max_length=1024, null=True)),
                ('content_type', models.ForeignKey(related_name='hs_geo_raster_resource_originalcoverage_related', to='contenttypes.ContentType')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='RasterMetaData',
            fields=[
                ('coremetadata_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='hs_core.CoreMetaData')),
            ],
            options={
            },
            bases=('hs_core.coremetadata',),
        ),
        migrations.CreateModel(
            name='RasterResource',
            fields=[
                ('page_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='pages.Page')),
                ('comments_count', models.IntegerField(default=0, editable=False)),
                ('rating_count', models.IntegerField(default=0, editable=False)),
                ('rating_sum', models.IntegerField(default=0, editable=False)),
                ('rating_average', models.FloatField(default=0, editable=False)),
                ('public', models.BooleanField(default=True, help_text=b'If this is true, the resource is viewable and downloadable by anyone')),
                ('frozen', models.BooleanField(default=False, help_text=b'If this is true, the resource should not be modified')),
                ('do_not_distribute', models.BooleanField(default=False, help_text=b'If this is true, the resource owner has to designate viewers')),
                ('discoverable', models.BooleanField(default=True, help_text=b'If this is true, it will turn up in searches.')),
                ('published_and_frozen', models.BooleanField(default=False, help_text=b'Once this is true, no changes can be made to the resource')),
                ('content', models.TextField()),
                ('short_id', models.CharField(default=hs_core.models.short_id, max_length=32, db_index=True)),
                ('doi', models.CharField(help_text=b"Permanent identifier. Never changes once it's been set.", max_length=1024, null=True, db_index=True, blank=True)),
                ('object_id', models.PositiveIntegerField(null=True, blank=True)),
                ('content_type', models.ForeignKey(blank=True, to='contenttypes.ContentType', null=True)),
                ('creator', models.ForeignKey(related_name='creator_of_hs_geo_raster_resource_rasterresource', to=settings.AUTH_USER_MODEL, help_text=b'This is the person who first uploaded the resource')),
                ('edit_groups', models.ManyToManyField(help_text=b'This is the set of CommonsShare Groups who can edit the resource', related_name='group_editable_hs_geo_raster_resource_rasterresource', null=True, to=b'auth.Group', blank=True)),
                ('edit_users', models.ManyToManyField(help_text=b'This is the set of CommonsShare Users who can edit the resource', related_name='user_editable_hs_geo_raster_resource_rasterresource', null=True, to=settings.AUTH_USER_MODEL, blank=True)),
                ('last_changed_by', models.ForeignKey(related_name='last_changed_hs_geo_raster_resource_rasterresource', to=settings.AUTH_USER_MODEL, help_text=b'The person who last changed the resource', null=True)),
                ('owners', models.ManyToManyField(help_text=b'The person who has total ownership of the resource', related_name='owns_hs_geo_raster_resource_rasterresource', to=settings.AUTH_USER_MODEL)),
                ('user', models.ForeignKey(related_name='rasterresources', verbose_name='Author', to=settings.AUTH_USER_MODEL)),
                ('view_groups', models.ManyToManyField(help_text=b'This is the set of CommonsShare Groups who can view the resource', related_name='group_viewable_hs_geo_raster_resource_rasterresource', null=True, to=b'auth.Group', blank=True)),
                ('view_users', models.ManyToManyField(help_text=b'This is the set of CommonsShare Users who can view the resource', related_name='user_viewable_hs_geo_raster_resource_rasterresource', null=True, to=settings.AUTH_USER_MODEL, blank=True)),
            ],
            options={
                'ordering': ('_order',),
                'verbose_name': 'Geographic Raster',
            },
            bases=('pages.page', models.Model),
        ),
        migrations.AlterUniqueTogether(
            name='originalcoverage',
            unique_together=set([('content_type', 'object_id')]),
        ),
        migrations.AlterUniqueTogether(
            name='cellinformation',
            unique_together=set([('content_type', 'object_id')]),
        ),
        migrations.RemoveField(
            model_name='cellinformation',
            name='cellSizeUnit',
        ),
    ]
