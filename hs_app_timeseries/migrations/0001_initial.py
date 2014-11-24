# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Site'
        db.create_table(u'hs_app_timeseries_site', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('object_id', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('content_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'])),
            ('site_code', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('site_name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('elevation_m', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('elevation_datum', self.gf('django.db.models.fields.CharField')(max_length=50, null=True, blank=True)),
            ('site_type', self.gf('django.db.models.fields.CharField')(max_length=100, null=True, blank=True)),
        ))
        db.send_create_signal(u'hs_app_timeseries', ['Site'])

        # Adding unique constraint on 'Site', fields ['content_type', 'object_id']
        db.create_unique(u'hs_app_timeseries_site', ['content_type_id', 'object_id'])

        # Adding model 'Variable'
        db.create_table(u'hs_app_timeseries_variable', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('object_id', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('content_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'])),
            ('variable_code', self.gf('django.db.models.fields.CharField')(max_length=20)),
            ('variable_name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('variable_type', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('no_data_value', self.gf('django.db.models.fields.IntegerField')()),
            ('variable_definition', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('speciation', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
        ))
        db.send_create_signal(u'hs_app_timeseries', ['Variable'])

        # Adding unique constraint on 'Variable', fields ['content_type', 'object_id']
        db.create_unique(u'hs_app_timeseries_variable', ['content_type_id', 'object_id'])

        # Adding model 'Method'
        db.create_table(u'hs_app_timeseries_method', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('object_id', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('content_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'])),
            ('method_code', self.gf('django.db.models.fields.IntegerField')()),
            ('method_name', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('method_type', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('method_description', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('method_link', self.gf('django.db.models.fields.URLField')(max_length=200, null=True, blank=True)),
        ))
        db.send_create_signal(u'hs_app_timeseries', ['Method'])

        # Adding unique constraint on 'Method', fields ['content_type', 'object_id']
        db.create_unique(u'hs_app_timeseries_method', ['content_type_id', 'object_id'])

        # Adding model 'ProcessingLevel'
        db.create_table(u'hs_app_timeseries_processinglevel', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('object_id', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('content_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'])),
            ('processing_level_code', self.gf('django.db.models.fields.IntegerField')()),
            ('definition', self.gf('django.db.models.fields.CharField')(max_length=200, null=True, blank=True)),
            ('explanation', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'hs_app_timeseries', ['ProcessingLevel'])

        # Adding unique constraint on 'ProcessingLevel', fields ['content_type', 'object_id']
        db.create_unique(u'hs_app_timeseries_processinglevel', ['content_type_id', 'object_id'])

        # Adding model 'TimeSeriesResult'
        db.create_table(u'hs_app_timeseries_timeseriesresult', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('object_id', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('content_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'])),
            ('units_type', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('units_name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('units_abbreviation', self.gf('django.db.models.fields.CharField')(max_length=20)),
            ('status', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('sample_medium', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('value_count', self.gf('django.db.models.fields.IntegerField')()),
            ('aggregation_statistics', self.gf('django.db.models.fields.CharField')(max_length=255)),
        ))
        db.send_create_signal(u'hs_app_timeseries', ['TimeSeriesResult'])

        # Adding unique constraint on 'TimeSeriesResult', fields ['content_type', 'object_id']
        db.create_unique(u'hs_app_timeseries_timeseriesresult', ['content_type_id', 'object_id'])

        # Adding model 'TimeSeriesResource'
        db.create_table(u'hs_app_timeseries_timeseriesresource', (
            (u'page_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['pages.Page'], unique=True, primary_key=True)),
            (u'comments_count', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('content', self.gf('mezzanine.core.fields.RichTextField')()),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'timeseriesresources', to=orm['auth.User'])),
            ('creator', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'creator_of_hs_app_timeseries_timeseriesresource', to=orm['auth.User'])),
            ('public', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('frozen', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('do_not_distribute', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('discoverable', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('published_and_frozen', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('last_changed_by', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'last_changed_hs_app_timeseries_timeseriesresource', null=True, to=orm['auth.User'])),
            ('short_id', self.gf('django.db.models.fields.CharField')(default='ea0d8fb0932245b8b790c41aa5b15130', max_length=32, db_index=True)),
            ('doi', self.gf('django.db.models.fields.CharField')(db_index=True, max_length=1024, null=True, blank=True)),
            ('object_id', self.gf('django.db.models.fields.PositiveIntegerField')(null=True, blank=True)),
            ('content_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'], null=True, blank=True)),
        ))
        db.send_create_signal(u'hs_app_timeseries', ['TimeSeriesResource'])

        # Adding M2M table for field owners on 'TimeSeriesResource'
        m2m_table_name = db.shorten_name(u'hs_app_timeseries_timeseriesresource_owners')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('timeseriesresource', models.ForeignKey(orm[u'hs_app_timeseries.timeseriesresource'], null=False)),
            ('user', models.ForeignKey(orm[u'auth.user'], null=False))
        ))
        db.create_unique(m2m_table_name, ['timeseriesresource_id', 'user_id'])

        # Adding M2M table for field view_users on 'TimeSeriesResource'
        m2m_table_name = db.shorten_name(u'hs_app_timeseries_timeseriesresource_view_users')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('timeseriesresource', models.ForeignKey(orm[u'hs_app_timeseries.timeseriesresource'], null=False)),
            ('user', models.ForeignKey(orm[u'auth.user'], null=False))
        ))
        db.create_unique(m2m_table_name, ['timeseriesresource_id', 'user_id'])

        # Adding M2M table for field view_groups on 'TimeSeriesResource'
        m2m_table_name = db.shorten_name(u'hs_app_timeseries_timeseriesresource_view_groups')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('timeseriesresource', models.ForeignKey(orm[u'hs_app_timeseries.timeseriesresource'], null=False)),
            ('group', models.ForeignKey(orm[u'auth.group'], null=False))
        ))
        db.create_unique(m2m_table_name, ['timeseriesresource_id', 'group_id'])

        # Adding M2M table for field edit_users on 'TimeSeriesResource'
        m2m_table_name = db.shorten_name(u'hs_app_timeseries_timeseriesresource_edit_users')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('timeseriesresource', models.ForeignKey(orm[u'hs_app_timeseries.timeseriesresource'], null=False)),
            ('user', models.ForeignKey(orm[u'auth.user'], null=False))
        ))
        db.create_unique(m2m_table_name, ['timeseriesresource_id', 'user_id'])

        # Adding M2M table for field edit_groups on 'TimeSeriesResource'
        m2m_table_name = db.shorten_name(u'hs_app_timeseries_timeseriesresource_edit_groups')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('timeseriesresource', models.ForeignKey(orm[u'hs_app_timeseries.timeseriesresource'], null=False)),
            ('group', models.ForeignKey(orm[u'auth.group'], null=False))
        ))
        db.create_unique(m2m_table_name, ['timeseriesresource_id', 'group_id'])

        # Adding model 'TimeSeriesMetaData'
        db.create_table(u'hs_app_timeseries_timeseriesmetadata', (
            (u'coremetadata_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['hs_core.CoreMetaData'], unique=True, primary_key=True)),
        ))
        db.send_create_signal(u'hs_app_timeseries', ['TimeSeriesMetaData'])


    def backwards(self, orm):
        # Removing unique constraint on 'TimeSeriesResult', fields ['content_type', 'object_id']
        db.delete_unique(u'hs_app_timeseries_timeseriesresult', ['content_type_id', 'object_id'])

        # Removing unique constraint on 'ProcessingLevel', fields ['content_type', 'object_id']
        db.delete_unique(u'hs_app_timeseries_processinglevel', ['content_type_id', 'object_id'])

        # Removing unique constraint on 'Method', fields ['content_type', 'object_id']
        db.delete_unique(u'hs_app_timeseries_method', ['content_type_id', 'object_id'])

        # Removing unique constraint on 'Variable', fields ['content_type', 'object_id']
        db.delete_unique(u'hs_app_timeseries_variable', ['content_type_id', 'object_id'])

        # Removing unique constraint on 'Site', fields ['content_type', 'object_id']
        db.delete_unique(u'hs_app_timeseries_site', ['content_type_id', 'object_id'])

        # Deleting model 'Site'
        db.delete_table(u'hs_app_timeseries_site')

        # Deleting model 'Variable'
        db.delete_table(u'hs_app_timeseries_variable')

        # Deleting model 'Method'
        db.delete_table(u'hs_app_timeseries_method')

        # Deleting model 'ProcessingLevel'
        db.delete_table(u'hs_app_timeseries_processinglevel')

        # Deleting model 'TimeSeriesResult'
        db.delete_table(u'hs_app_timeseries_timeseriesresult')

        # Deleting model 'TimeSeriesResource'
        db.delete_table(u'hs_app_timeseries_timeseriesresource')

        # Removing M2M table for field owners on 'TimeSeriesResource'
        db.delete_table(db.shorten_name(u'hs_app_timeseries_timeseriesresource_owners'))

        # Removing M2M table for field view_users on 'TimeSeriesResource'
        db.delete_table(db.shorten_name(u'hs_app_timeseries_timeseriesresource_view_users'))

        # Removing M2M table for field view_groups on 'TimeSeriesResource'
        db.delete_table(db.shorten_name(u'hs_app_timeseries_timeseriesresource_view_groups'))

        # Removing M2M table for field edit_users on 'TimeSeriesResource'
        db.delete_table(db.shorten_name(u'hs_app_timeseries_timeseriesresource_edit_users'))

        # Removing M2M table for field edit_groups on 'TimeSeriesResource'
        db.delete_table(db.shorten_name(u'hs_app_timeseries_timeseriesresource_edit_groups'))

        # Deleting model 'TimeSeriesMetaData'
        db.delete_table(u'hs_app_timeseries_timeseriesmetadata')


    models = {
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Group']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Permission']"}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'hs_app_timeseries.method': {
            'Meta': {'unique_together': "(('content_type', 'object_id'),)", 'object_name': 'Method'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'method_code': ('django.db.models.fields.IntegerField', [], {}),
            'method_description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'method_link': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'method_name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'method_type': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {})
        },
        u'hs_app_timeseries.processinglevel': {
            'Meta': {'unique_together': "(('content_type', 'object_id'),)", 'object_name': 'ProcessingLevel'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            'definition': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'explanation': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'processing_level_code': ('django.db.models.fields.IntegerField', [], {})
        },
        u'hs_app_timeseries.site': {
            'Meta': {'unique_together': "(('content_type', 'object_id'),)", 'object_name': 'Site'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            'elevation_datum': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'elevation_m': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'site_code': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'site_name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'site_type': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'})
        },
        u'hs_app_timeseries.timeseriesmetadata': {
            'Meta': {'object_name': 'TimeSeriesMetaData', '_ormbases': [u'hs_core.CoreMetaData']},
            u'coremetadata_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['hs_core.CoreMetaData']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'hs_app_timeseries.timeseriesresource': {
            'Meta': {'ordering': "(u'_order',)", 'object_name': 'TimeSeriesResource', '_ormbases': [u'pages.Page']},
            u'comments_count': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'content': ('mezzanine.core.fields.RichTextField', [], {}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']", 'null': 'True', 'blank': 'True'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'creator_of_hs_app_timeseries_timeseriesresource'", 'to': u"orm['auth.User']"}),
            'discoverable': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'do_not_distribute': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'doi': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '1024', 'null': 'True', 'blank': 'True'}),
            'edit_groups': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "u'group_editable_hs_app_timeseries_timeseriesresource'", 'null': 'True', 'symmetrical': 'False', 'to': u"orm['auth.Group']"}),
            'edit_users': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "u'user_editable_hs_app_timeseries_timeseriesresource'", 'null': 'True', 'symmetrical': 'False', 'to': u"orm['auth.User']"}),
            'frozen': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_changed_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'last_changed_hs_app_timeseries_timeseriesresource'", 'null': 'True', 'to': u"orm['auth.User']"}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'owners': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "u'owns_hs_app_timeseries_timeseriesresource'", 'symmetrical': 'False', 'to': u"orm['auth.User']"}),
            u'page_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['pages.Page']", 'unique': 'True', 'primary_key': 'True'}),
            'public': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'published_and_frozen': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'short_id': ('django.db.models.fields.CharField', [], {'default': "'715b00eaf1744f589f018bfda6995ba6'", 'max_length': '32', 'db_index': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'timeseriesresources'", 'to': u"orm['auth.User']"}),
            'view_groups': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "u'group_viewable_hs_app_timeseries_timeseriesresource'", 'null': 'True', 'symmetrical': 'False', 'to': u"orm['auth.Group']"}),
            'view_users': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "u'user_viewable_hs_app_timeseries_timeseriesresource'", 'null': 'True', 'symmetrical': 'False', 'to': u"orm['auth.User']"})
        },
        u'hs_app_timeseries.timeseriesresult': {
            'Meta': {'unique_together': "(('content_type', 'object_id'),)", 'object_name': 'TimeSeriesResult'},
            'aggregation_statistics': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'sample_medium': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'units_abbreviation': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'units_name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'units_type': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'value_count': ('django.db.models.fields.IntegerField', [], {})
        },
        u'hs_app_timeseries.variable': {
            'Meta': {'unique_together': "(('content_type', 'object_id'),)", 'object_name': 'Variable'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'no_data_value': ('django.db.models.fields.IntegerField', [], {}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'speciation': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'variable_code': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'variable_definition': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'variable_name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'variable_type': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'hs_core.coremetadata': {
            'Meta': {'object_name': 'CoreMetaData'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        u'pages.page': {
            'Meta': {'ordering': "(u'titles',)", 'object_name': 'Page'},
            '_meta_title': ('django.db.models.fields.CharField', [], {'max_length': '500', 'null': 'True', 'blank': 'True'}),
            '_order': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'content_model': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'expiry_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'gen_description': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'in_menus': ('mezzanine.pages.fields.MenusField', [], {'default': '(1, 2, 3)', 'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'in_sitemap': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            u'keywords_string': ('django.db.models.fields.CharField', [], {'max_length': '500', 'blank': 'True'}),
            'login_required': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "u'children'", 'null': 'True', 'to': u"orm['pages.Page']"}),
            'publish_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'short_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'site': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['sites.Site']"}),
            'slug': ('django.db.models.fields.CharField', [], {'max_length': '2000', 'null': 'True', 'blank': 'True'}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '2'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
            'titles': ('django.db.models.fields.CharField', [], {'max_length': '1000', 'null': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'null': 'True'})
        },
        u'sites.site': {
            'Meta': {'ordering': "(u'domain',)", 'object_name': 'Site', 'db_table': "u'django_site'"},
            'domain': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        }
    }

    complete_apps = ['hs_app_timeseries']