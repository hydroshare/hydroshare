# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'InstResource'
        db.create_table(u'hs_rhessys_inst_resource_instresource', (
            (u'page_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['pages.Page'], unique=True, primary_key=True)),
            (u'comments_count', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('content', self.gf('mezzanine.core.fields.RichTextField')()),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'instresources', to=orm['auth.User'])),
            ('creator', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'creator_of_hs_rhessys_inst_resource_instresource', to=orm['auth.User'])),
            ('public', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('frozen', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('do_not_distribute', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('discoverable', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('published_and_frozen', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('last_changed_by', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'last_changed_hs_rhessys_inst_resource_instresource', null=True, to=orm['auth.User'])),
            ('short_id', self.gf('django.db.models.fields.CharField')(default='d8b7d355d5344eda92e3ab4f66b7b386', max_length=32, db_index=True)),
            ('doi', self.gf('django.db.models.fields.CharField')(db_index=True, max_length=1024, null=True, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('git_repo', self.gf('django.db.models.fields.URLField')(max_length=200)),
            ('git_username', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('git_password', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('commit_id', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('model_desc', self.gf('django.db.models.fields.CharField')(max_length=500)),
            ('git_branch', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('study_area_bbox', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('model_command_line_parameters', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('project_name', self.gf('django.db.models.fields.CharField')(max_length=100)),
        ))
        db.send_create_signal(u'hs_rhessys_inst_resource', ['InstResource'])

        # Adding M2M table for field owners on 'InstResource'
        m2m_table_name = db.shorten_name(u'hs_rhessys_inst_resource_instresource_owners')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('instresource', models.ForeignKey(orm[u'hs_rhessys_inst_resource.instresource'], null=False)),
            ('user', models.ForeignKey(orm[u'auth.user'], null=False))
        ))
        db.create_unique(m2m_table_name, ['instresource_id', 'user_id'])

        # Adding M2M table for field view_users on 'InstResource'
        m2m_table_name = db.shorten_name(u'hs_rhessys_inst_resource_instresource_view_users')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('instresource', models.ForeignKey(orm[u'hs_rhessys_inst_resource.instresource'], null=False)),
            ('user', models.ForeignKey(orm[u'auth.user'], null=False))
        ))
        db.create_unique(m2m_table_name, ['instresource_id', 'user_id'])

        # Adding M2M table for field view_groups on 'InstResource'
        m2m_table_name = db.shorten_name(u'hs_rhessys_inst_resource_instresource_view_groups')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('instresource', models.ForeignKey(orm[u'hs_rhessys_inst_resource.instresource'], null=False)),
            ('group', models.ForeignKey(orm[u'auth.group'], null=False))
        ))
        db.create_unique(m2m_table_name, ['instresource_id', 'group_id'])

        # Adding M2M table for field edit_users on 'InstResource'
        m2m_table_name = db.shorten_name(u'hs_rhessys_inst_resource_instresource_edit_users')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('instresource', models.ForeignKey(orm[u'hs_rhessys_inst_resource.instresource'], null=False)),
            ('user', models.ForeignKey(orm[u'auth.user'], null=False))
        ))
        db.create_unique(m2m_table_name, ['instresource_id', 'user_id'])

        # Adding M2M table for field edit_groups on 'InstResource'
        m2m_table_name = db.shorten_name(u'hs_rhessys_inst_resource_instresource_edit_groups')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('instresource', models.ForeignKey(orm[u'hs_rhessys_inst_resource.instresource'], null=False)),
            ('group', models.ForeignKey(orm[u'auth.group'], null=False))
        ))
        db.create_unique(m2m_table_name, ['instresource_id', 'group_id'])


    def backwards(self, orm):
        # Deleting model 'InstResource'
        db.delete_table(u'hs_rhessys_inst_resource_instresource')

        # Removing M2M table for field owners on 'InstResource'
        db.delete_table(db.shorten_name(u'hs_rhessys_inst_resource_instresource_owners'))

        # Removing M2M table for field view_users on 'InstResource'
        db.delete_table(db.shorten_name(u'hs_rhessys_inst_resource_instresource_view_users'))

        # Removing M2M table for field view_groups on 'InstResource'
        db.delete_table(db.shorten_name(u'hs_rhessys_inst_resource_instresource_view_groups'))

        # Removing M2M table for field edit_users on 'InstResource'
        db.delete_table(db.shorten_name(u'hs_rhessys_inst_resource_instresource_edit_users'))

        # Removing M2M table for field edit_groups on 'InstResource'
        db.delete_table(db.shorten_name(u'hs_rhessys_inst_resource_instresource_edit_groups'))


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
        u'hs_rhessys_inst_resource.instresource': {
            'Meta': {'ordering': "(u'_order',)", 'object_name': 'InstResource', '_ormbases': [u'pages.Page']},
            u'comments_count': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'commit_id': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'content': ('mezzanine.core.fields.RichTextField', [], {}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'creator_of_hs_rhessys_inst_resource_instresource'", 'to': u"orm['auth.User']"}),
            'discoverable': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'do_not_distribute': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'doi': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '1024', 'null': 'True', 'blank': 'True'}),
            'edit_groups': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "u'group_editable_hs_rhessys_inst_resource_instresource'", 'null': 'True', 'symmetrical': 'False', 'to': u"orm['auth.Group']"}),
            'edit_users': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "u'user_editable_hs_rhessys_inst_resource_instresource'", 'null': 'True', 'symmetrical': 'False', 'to': u"orm['auth.User']"}),
            'frozen': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'git_branch': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'git_password': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'git_repo': ('django.db.models.fields.URLField', [], {'max_length': '200'}),
            'git_username': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'last_changed_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'last_changed_hs_rhessys_inst_resource_instresource'", 'null': 'True', 'to': u"orm['auth.User']"}),
            'model_command_line_parameters': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'model_desc': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'owners': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "u'owns_hs_rhessys_inst_resource_instresource'", 'symmetrical': 'False', 'to': u"orm['auth.User']"}),
            u'page_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['pages.Page']", 'unique': 'True', 'primary_key': 'True'}),
            'project_name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'public': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'published_and_frozen': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'short_id': ('django.db.models.fields.CharField', [], {'default': "'4f9ef060610745fda47e649219420b5b'", 'max_length': '32', 'db_index': 'True'}),
            'study_area_bbox': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'instresources'", 'to': u"orm['auth.User']"}),
            'view_groups': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "u'group_viewable_hs_rhessys_inst_resource_instresource'", 'null': 'True', 'symmetrical': 'False', 'to': u"orm['auth.Group']"}),
            'view_users': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "u'user_viewable_hs_rhessys_inst_resource_instresource'", 'null': 'True', 'symmetrical': 'False', 'to': u"orm['auth.User']"})
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

    complete_apps = ['hs_rhessys_inst_resource']