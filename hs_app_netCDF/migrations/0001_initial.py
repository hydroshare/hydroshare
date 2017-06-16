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
            name='NetcdfMetaData',
            fields=[
                ('coremetadata_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='hs_core.CoreMetaData')),
            ],
            options={
            },
            bases=('hs_core.coremetadata',),
        ),
        migrations.CreateModel(
            name='NetcdfResource',
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
                ('creator', models.ForeignKey(related_name='creator_of_hs_app_netcdf_netcdfresource', to=settings.AUTH_USER_MODEL, help_text=b'This is the person who first uploaded the resource')),
                ('edit_groups', models.ManyToManyField(help_text=b'This is the set of xDCIShare Groups who can edit the resource', related_name='group_editable_hs_app_netcdf_netcdfresource', null=True, to='auth.Group', blank=True)),
                ('edit_users', models.ManyToManyField(help_text=b'This is the set of xDCIShare Users who can edit the resource', related_name='user_editable_hs_app_netcdf_netcdfresource', null=True, to=settings.AUTH_USER_MODEL, blank=True)),
                ('last_changed_by', models.ForeignKey(related_name='last_changed_hs_app_netcdf_netcdfresource', to=settings.AUTH_USER_MODEL, help_text=b'The person who last changed the resource', null=True)),
                ('owners', models.ManyToManyField(help_text=b'The person who has total ownership of the resource', related_name='owns_hs_app_netcdf_netcdfresource', to=settings.AUTH_USER_MODEL)),
                ('user', models.ForeignKey(related_name='netcdfresources', verbose_name='Author', to=settings.AUTH_USER_MODEL)),
                ('view_groups', models.ManyToManyField(help_text=b'This is the set of xDCIShare Groups who can view the resource', related_name='group_viewable_hs_app_netcdf_netcdfresource', null=True, to='auth.Group', blank=True)),
                ('view_users', models.ManyToManyField(help_text=b'This is the set of xDCIShare Users who can view the resource', related_name='user_viewable_hs_app_netcdf_netcdfresource', null=True, to=settings.AUTH_USER_MODEL, blank=True)),
            ],
            options={
                'ordering': ('_order',),
                'verbose_name': 'Multidimensional (NetCDF)',
            },
            bases=('pages.page', models.Model),
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
            options={
            },
            bases=(models.Model,),
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
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='originalcoverage',
            unique_together=set([('content_type', 'object_id')]),
        ),
    ]
