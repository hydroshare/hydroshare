# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'RasterBand'
        db.create_table(u'hs_geo_raster_resource_rasterband', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('bandName', self.gf('django.db.models.fields.CharField')(max_length=50, null=True)),
            ('variableName', self.gf('django.db.models.fields.CharField')(max_length=50, null=True)),
            ('variableUnit', self.gf('django.db.models.fields.CharField')(max_length=50, null=True)),
            ('method', self.gf('django.db.models.fields.TextField')(null=True)),
            ('comment', self.gf('django.db.models.fields.TextField')(null=True)),
        ))
        db.send_create_signal(u'hs_geo_raster_resource', ['RasterBand'])

        # Adding model 'RasterResource'
        db.create_table(u'hs_geo_raster_resource_rasterresource', (
            (u'page_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['pages.Page'], unique=True, primary_key=True)),
            (u'comments_count', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'rasterresources', to=orm['auth.User'])),
            ('creator', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'creator_of_hs_geo_raster_resource_rasterresource', to=orm['auth.User'])),
            ('public', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('frozen', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('do_not_distribute', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('discoverable', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('published_and_frozen', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('content', self.gf('django.db.models.fields.TextField')()),
            ('last_changed_by', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'last_changed_hs_geo_raster_resource_rasterresource', null=True, to=orm['auth.User'])),
            ('short_id', self.gf('django.db.models.fields.CharField')(default='fd2881d7fc064cbaae59b66350bf63ac', max_length=32, db_index=True)),
            ('doi', self.gf('django.db.models.fields.CharField')(db_index=True, max_length=1024, null=True, blank=True)),
            ('object_id', self.gf('django.db.models.fields.PositiveIntegerField')(null=True, blank=True)),
            ('content_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'], null=True, blank=True)),
            ('rows', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('columns', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('cellSizeXValue', self.gf('django.db.models.fields.FloatField')(null=True)),
            ('cellSizeYValue', self.gf('django.db.models.fields.FloatField')(null=True)),
            ('cellSizeUnit', self.gf('django.db.models.fields.CharField')(max_length=50, null=True)),
            ('cellDataType', self.gf('django.db.models.fields.CharField')(max_length=50, null=True)),
            ('noDataValue', self.gf('django.db.models.fields.FloatField')(null=True)),
            ('bandCount', self.gf('django.db.models.fields.IntegerField')(null=True)),
        ))
        db.send_create_signal(u'hs_geo_raster_resource', ['RasterResource'])

        # Adding M2M table for field owners on 'RasterResource'
        m2m_table_name = db.shorten_name(u'hs_geo_raster_resource_rasterresource_owners')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('rasterresource', models.ForeignKey(orm[u'hs_geo_raster_resource.rasterresource'], null=False)),
            ('user', models.ForeignKey(orm[u'auth.user'], null=False))
        ))
        db.create_unique(m2m_table_name, ['rasterresource_id', 'user_id'])

        # Adding M2M table for field view_users on 'RasterResource'
        m2m_table_name = db.shorten_name(u'hs_geo_raster_resource_rasterresource_view_users')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('rasterresource', models.ForeignKey(orm[u'hs_geo_raster_resource.rasterresource'], null=False)),
            ('user', models.ForeignKey(orm[u'auth.user'], null=False))
        ))
        db.create_unique(m2m_table_name, ['rasterresource_id', 'user_id'])

        # Adding M2M table for field view_groups on 'RasterResource'
        m2m_table_name = db.shorten_name(u'hs_geo_raster_resource_rasterresource_view_groups')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('rasterresource', models.ForeignKey(orm[u'hs_geo_raster_resource.rasterresource'], null=False)),
            ('group', models.ForeignKey(orm[u'auth.group'], null=False))
        ))
        db.create_unique(m2m_table_name, ['rasterresource_id', 'group_id'])

        # Adding M2M table for field edit_users on 'RasterResource'
        m2m_table_name = db.shorten_name(u'hs_geo_raster_resource_rasterresource_edit_users')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('rasterresource', models.ForeignKey(orm[u'hs_geo_raster_resource.rasterresource'], null=False)),
            ('user', models.ForeignKey(orm[u'auth.user'], null=False))
        ))
        db.create_unique(m2m_table_name, ['rasterresource_id', 'user_id'])

        # Adding M2M table for field edit_groups on 'RasterResource'
        m2m_table_name = db.shorten_name(u'hs_geo_raster_resource_rasterresource_edit_groups')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('rasterresource', models.ForeignKey(orm[u'hs_geo_raster_resource.rasterresource'], null=False)),
            ('group', models.ForeignKey(orm[u'auth.group'], null=False))
        ))
        db.create_unique(m2m_table_name, ['rasterresource_id', 'group_id'])

        # Adding M2M table for field bands on 'RasterResource'
        m2m_table_name = db.shorten_name(u'hs_geo_raster_resource_rasterresource_bands')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('rasterresource', models.ForeignKey(orm[u'hs_geo_raster_resource.rasterresource'], null=False)),
            ('rasterband', models.ForeignKey(orm[u'hs_geo_raster_resource.rasterband'], null=False))
        ))
        db.create_unique(m2m_table_name, ['rasterresource_id', 'rasterband_id'])


    def backwards(self, orm):
        # Deleting model 'RasterBand'
        db.delete_table(u'hs_geo_raster_resource_rasterband')

        # Deleting model 'RasterResource'
        db.delete_table(u'hs_geo_raster_resource_rasterresource')

        # Removing M2M table for field owners on 'RasterResource'
        db.delete_table(db.shorten_name(u'hs_geo_raster_resource_rasterresource_owners'))

        # Removing M2M table for field view_users on 'RasterResource'
        db.delete_table(db.shorten_name(u'hs_geo_raster_resource_rasterresource_view_users'))

        # Removing M2M table for field view_groups on 'RasterResource'
        db.delete_table(db.shorten_name(u'hs_geo_raster_resource_rasterresource_view_groups'))

        # Removing M2M table for field edit_users on 'RasterResource'
        db.delete_table(db.shorten_name(u'hs_geo_raster_resource_rasterresource_edit_users'))

        # Removing M2M table for field edit_groups on 'RasterResource'
        db.delete_table(db.shorten_name(u'hs_geo_raster_resource_rasterresource_edit_groups'))

        # Removing M2M table for field bands on 'RasterResource'
        db.delete_table(db.shorten_name(u'hs_geo_raster_resource_rasterresource_bands'))


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
        u'hs_geo_raster_resource.rasterband': {
            'Meta': {'object_name': 'RasterBand'},
            'bandName': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True'}),
            'comment': ('django.db.models.fields.TextField', [], {'null': 'True'}),
             u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'method': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'variableName': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True'}),
            'variableUnit': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True'})
        },
        u'hs_geo_raster_resource.rasterresource': {
            'Meta': {'ordering': "(u'_order',)", 'object_name': 'RasterResource', '_ormbases': [u'pages.Page']},
            'bandCount': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'bands': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'bands_of_raster'", 'symmetrical': 'False', 'to': u"orm['hs_geo_raster_resource.RasterBand']"}),
            'cellDataType': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True'}),
            'noDataValue': ('django.db.models.fields.FloatField', [], {'null': 'True'}),
            'cellSizeUnit': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True'}),
            'cellSizeXValue': ('django.db.models.fields.FloatField', [], {'null': 'True'}),
            'cellSizeYValue': ('django.db.models.fields.FloatField', [], {'null': 'True'}),
            'columns': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            u'comments_count': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'content': ('django.db.models.fields.TextField', [], {}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']", 'null': 'True', 'blank': 'True'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'creator_of_hs_geo_raster_resource_rasterresource'", 'to': u"orm['auth.User']"}),
            'discoverable': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'do_not_distribute': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'doi': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '1024', 'null': 'True', 'blank': 'True'}),
            'edit_groups': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "u'group_editable_hs_geo_raster_resource_rasterresource'", 'null': 'True', 'symmetrical': 'False', 'to': u"orm['auth.Group']"}),
            'edit_users': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "u'user_editable_hs_geo_raster_resource_rasterresource'", 'null': 'True', 'symmetrical': 'False', 'to': u"orm['auth.User']"}),
            'frozen': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_changed_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'last_changed_hs_geo_raster_resource_rasterresource'", 'null': 'True', 'to': u"orm['auth.User']"}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'owners': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "u'owns_hs_geo_raster_resource_rasterresource'", 'symmetrical': 'False', 'to': u"orm['auth.User']"}),
            u'page_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['pages.Page']", 'unique': 'True', 'primary_key': 'True'}),
            'public': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'published_and_frozen': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'rows': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'short_id': ('django.db.models.fields.CharField', [], {'default': "'a4955dbad8bb40bbb1077ac6c37f9fd0'", 'max_length': '32', 'db_index': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'rasterresources'", 'to': u"orm['auth.User']"}),
            'view_groups': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "u'group_viewable_hs_geo_raster_resource_rasterresource'", 'null': 'True', 'symmetrical': 'False', 'to': u"orm['auth.Group']"}),
            'view_users': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "u'user_viewable_hs_geo_raster_resource_rasterresource'", 'null': 'True', 'symmetrical': 'False', 'to': u"orm['auth.User']"})
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

    complete_apps = ['hs_geo_raster_resource']