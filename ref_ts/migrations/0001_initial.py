# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings
import hs_core.models
import mezzanine.core.fields


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
            name='Method',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('value', models.CharField(max_length=200)),
                ('content_type', models.ForeignKey(to='contenttypes.ContentType')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='QualityControlLevel',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('value', models.CharField(max_length=200)),
                ('content_type', models.ForeignKey(to='contenttypes.ContentType')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='RefTimeSeries',
            fields=[
                ('page_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='pages.Page')),
                ('comments_count', models.IntegerField(default=0, editable=False)),
                ('content', mezzanine.core.fields.RichTextField(verbose_name='Content')),
                ('public', models.BooleanField(default=True, help_text=b'If this is true, the resource is viewable and downloadable by anyone')),
                ('frozen', models.BooleanField(default=False, help_text=b'If this is true, the resource should not be modified')),
                ('do_not_distribute', models.BooleanField(default=False, help_text=b'If this is true, the resource owner has to designate viewers')),
                ('discoverable', models.BooleanField(default=True, help_text=b'If this is true, it will turn up in searches.')),
                ('published_and_frozen', models.BooleanField(default=False, help_text=b'Once this is true, no changes can be made to the resource')),
                ('short_id', models.CharField(default=hs_core.models.short_id, max_length=32, db_index=True)),
                ('doi', models.CharField(help_text=b"Permanent identifier. Never changes once it's been set.", max_length=1024, null=True, db_index=True, blank=True)),
                ('object_id', models.PositiveIntegerField(null=True, blank=True)),
                ('reference_type', models.CharField(default=b'', max_length=4, blank=True)),
                ('url', models.URLField(default=b'', verbose_name=b'Web Services Url', blank=True)),
                ('data_site_name', models.CharField(default=b'', max_length=100, null=True, verbose_name=b'Time Series Site value', blank=True)),
                ('data_site_code', models.CharField(default=b'', max_length=100, null=True, verbose_name=b'Time Series Site Code', blank=True)),
                ('variable_name', models.CharField(default=b'', max_length=100, null=True, verbose_name=b'Data Variable Name', blank=True)),
                ('variable_code', models.CharField(default=b'', max_length=100, null=True, verbose_name=b'Data Variable Code', blank=True)),
                ('start_date', models.DateTimeField(null=True)),
                ('end_date', models.DateTimeField(null=True)),
                ('content_type', models.ForeignKey(blank=True, to='contenttypes.ContentType', null=True)),
                ('creator', models.ForeignKey(related_name='creator_of_ref_ts_reftimeseries', to=settings.AUTH_USER_MODEL, help_text=b'This is the person who first uploaded the resource')),
                ('edit_groups', models.ManyToManyField(help_text=b'This is the set of Hydroshare Groups who can edit the resource', related_name='group_editable_ref_ts_reftimeseries', null=True, to='auth.Group', blank=True)),
                ('edit_users', models.ManyToManyField(help_text=b'This is the set of Hydroshare Users who can edit the resource', related_name='user_editable_ref_ts_reftimeseries', null=True, to=settings.AUTH_USER_MODEL, blank=True)),
                ('last_changed_by', models.ForeignKey(related_name='last_changed_ref_ts_reftimeseries', to=settings.AUTH_USER_MODEL, help_text=b'The person who last changed the resource', null=True)),
                ('owners', models.ManyToManyField(help_text=b'The person who uploaded the resource', related_name='owns_ref_ts_reftimeseries', to=settings.AUTH_USER_MODEL)),
                ('user', models.ForeignKey(related_name='reftimeseriess', verbose_name='Author', to=settings.AUTH_USER_MODEL)),
                ('view_groups', models.ManyToManyField(help_text=b'This is the set of Hydroshare Groups who can view the resource', related_name='group_viewable_ref_ts_reftimeseries', null=True, to='auth.Group', blank=True)),
                ('view_users', models.ManyToManyField(help_text=b'This is the set of Hydroshare Users who can view the resource', related_name='user_viewable_ref_ts_reftimeseries', null=True, to=settings.AUTH_USER_MODEL, blank=True)),
            ],
            options={
                'ordering': ('_order',),
                'verbose_name': 'Referenced HIS Time Series Resource',
            },
            bases=('pages.page', models.Model),
        ),
        migrations.CreateModel(
            name='RefTSMetadata',
            fields=[
                ('coremetadata_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='hs_core.CoreMetaData')),
                ('_refts_resource', models.ManyToManyField(to='ref_ts.RefTimeSeries')),
                ('methods', models.ManyToManyField(to='ref_ts.Method')),
                ('quality_levels', models.ManyToManyField(to='ref_ts.QualityControlLevel')),
            ],
            options={
            },
            bases=('hs_core.coremetadata',),
        ),
        migrations.CreateModel(
            name='Site',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('name', models.CharField(max_length=100)),
                ('code', models.CharField(max_length=50)),
                ('latitude', models.DecimalField(null=True, max_digits=9, decimal_places=6)),
                ('longitude', models.DecimalField(null=True, max_digits=9, decimal_places=6)),
                ('content_type', models.ForeignKey(to='contenttypes.ContentType')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Variable',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('name', models.CharField(max_length=100)),
                ('code', models.CharField(max_length=50)),
                ('data_type', models.CharField(max_length=50, null=True)),
                ('sample_medium', models.CharField(max_length=50, null=True)),
                ('content_type', models.ForeignKey(to='contenttypes.ContentType')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='reftsmetadata',
            name='sites',
            field=models.ManyToManyField(to='ref_ts.Site'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='reftsmetadata',
            name='variables',
            field=models.ManyToManyField(to='ref_ts.Variable'),
            preserve_default=True,
        ),
    ]
