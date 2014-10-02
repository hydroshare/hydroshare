# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):

        # Changing field 'Contributor.description'
        db.alter_column(u'hs_core_contributor', 'description', self.gf('django.db.models.fields.URLField')(max_length=200, null=True))

        # Changing field 'Contributor.researchGateID'
        db.alter_column(u'hs_core_contributor', 'researchGateID', self.gf('django.db.models.fields.URLField')(max_length=200, null=True))

        # Changing field 'Contributor.phone'
        db.alter_column(u'hs_core_contributor', 'phone', self.gf('django.db.models.fields.CharField')(max_length=25, null=True))

        # Changing field 'Contributor.address'
        db.alter_column(u'hs_core_contributor', 'address', self.gf('django.db.models.fields.CharField')(max_length=250, null=True))

        # Changing field 'Contributor.organization'
        db.alter_column(u'hs_core_contributor', 'organization', self.gf('django.db.models.fields.CharField')(max_length=200, null=True))

        # Changing field 'Contributor.homepage'
        db.alter_column(u'hs_core_contributor', 'homepage', self.gf('django.db.models.fields.URLField')(max_length=200, null=True))

        # Changing field 'Contributor.email'
        db.alter_column(u'hs_core_contributor', 'email', self.gf('django.db.models.fields.EmailField')(max_length=75, null=True))

        # Changing field 'Contributor.researcherID'
        db.alter_column(u'hs_core_contributor', 'researcherID', self.gf('django.db.models.fields.URLField')(max_length=200, null=True))

        # Changing field 'Creator.description'
        db.alter_column(u'hs_core_creator', 'description', self.gf('django.db.models.fields.URLField')(max_length=200, null=True))

        # Changing field 'Creator.researchGateID'
        db.alter_column(u'hs_core_creator', 'researchGateID', self.gf('django.db.models.fields.URLField')(max_length=200, null=True))

        # Changing field 'Creator.phone'
        db.alter_column(u'hs_core_creator', 'phone', self.gf('django.db.models.fields.CharField')(max_length=25, null=True))

        # Changing field 'Creator.address'
        db.alter_column(u'hs_core_creator', 'address', self.gf('django.db.models.fields.CharField')(max_length=250, null=True))

        # Changing field 'Creator.organization'
        db.alter_column(u'hs_core_creator', 'organization', self.gf('django.db.models.fields.CharField')(max_length=200, null=True))

        # Changing field 'Creator.homepage'
        db.alter_column(u'hs_core_creator', 'homepage', self.gf('django.db.models.fields.URLField')(max_length=200, null=True))

        # Changing field 'Creator.email'
        db.alter_column(u'hs_core_creator', 'email', self.gf('django.db.models.fields.EmailField')(max_length=75, null=True))

        # Changing field 'Creator.researcherID'
        db.alter_column(u'hs_core_creator', 'researcherID', self.gf('django.db.models.fields.URLField')(max_length=200, null=True))

        # Changing field 'Rights.url'
        db.alter_column(u'hs_core_rights', 'url', self.gf('django.db.models.fields.URLField')(max_length=200, null=True))

        # Changing field 'Rights.statement'
        db.alter_column(u'hs_core_rights', 'statement', self.gf('django.db.models.fields.TextField')(null=True))
        # Deleting field 'Coverage.value'
        db.delete_column(u'hs_core_coverage', 'value')

        # Adding field 'Coverage._value'
        db.add_column(u'hs_core_coverage', '_value',
                      self.gf('django.db.models.fields.CharField')(default='[]', max_length=1024),
                      keep_default=False)

        # Deleting field 'GenericResource.metadata'
        db.delete_column(u'hs_core_genericresource', 'metadata_id')

        # Adding field 'GenericResource.object_id'
        db.add_column(u'hs_core_genericresource', 'object_id',
                      self.gf('django.db.models.fields.PositiveIntegerField')(null=True, blank=True),
                      keep_default=False)

        # Adding field 'GenericResource.content_type'
        db.add_column(u'hs_core_genericresource', 'content_type',
                      self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'], null=True, blank=True),
                      keep_default=False)


    def backwards(self, orm):

        # Changing field 'Contributor.description'
        db.alter_column(u'hs_core_contributor', 'description', self.gf('django.db.models.fields.URLField')(default='', max_length=200))

        # Changing field 'Contributor.researchGateID'
        db.alter_column(u'hs_core_contributor', 'researchGateID', self.gf('django.db.models.fields.URLField')(default='', max_length=200))

        # Changing field 'Contributor.phone'
        db.alter_column(u'hs_core_contributor', 'phone', self.gf('django.db.models.fields.CharField')(default='', max_length=25))

        # Changing field 'Contributor.address'
        db.alter_column(u'hs_core_contributor', 'address', self.gf('django.db.models.fields.CharField')(default='', max_length=250))

        # Changing field 'Contributor.organization'
        db.alter_column(u'hs_core_contributor', 'organization', self.gf('django.db.models.fields.CharField')(default='', max_length=200))

        # Changing field 'Contributor.homepage'
        db.alter_column(u'hs_core_contributor', 'homepage', self.gf('django.db.models.fields.URLField')(default='', max_length=200))

        # Changing field 'Contributor.email'
        db.alter_column(u'hs_core_contributor', 'email', self.gf('django.db.models.fields.EmailField')(default='', max_length=75))

        # Changing field 'Contributor.researcherID'
        db.alter_column(u'hs_core_contributor', 'researcherID', self.gf('django.db.models.fields.URLField')(default='', max_length=200))

        # Changing field 'Creator.description'
        db.alter_column(u'hs_core_creator', 'description', self.gf('django.db.models.fields.URLField')(default='', max_length=200))

        # Changing field 'Creator.researchGateID'
        db.alter_column(u'hs_core_creator', 'researchGateID', self.gf('django.db.models.fields.URLField')(default='', max_length=200))

        # Changing field 'Creator.phone'
        db.alter_column(u'hs_core_creator', 'phone', self.gf('django.db.models.fields.CharField')(default='', max_length=25))

        # Changing field 'Creator.address'
        db.alter_column(u'hs_core_creator', 'address', self.gf('django.db.models.fields.CharField')(default='', max_length=250))

        # Changing field 'Creator.organization'
        db.alter_column(u'hs_core_creator', 'organization', self.gf('django.db.models.fields.CharField')(default='', max_length=200))

        # Changing field 'Creator.homepage'
        db.alter_column(u'hs_core_creator', 'homepage', self.gf('django.db.models.fields.URLField')(default='', max_length=200))

        # Changing field 'Creator.email'
        db.alter_column(u'hs_core_creator', 'email', self.gf('django.db.models.fields.EmailField')(default='', max_length=75))

        # Changing field 'Creator.researcherID'
        db.alter_column(u'hs_core_creator', 'researcherID', self.gf('django.db.models.fields.URLField')(default='', max_length=200))

        # Changing field 'Rights.url'
        db.alter_column(u'hs_core_rights', 'url', self.gf('django.db.models.fields.URLField')(default='', max_length=200))

        # Changing field 'Rights.statement'
        db.alter_column(u'hs_core_rights', 'statement', self.gf('django.db.models.fields.TextField')(default=''))

        # User chose to not deal with backwards NULL issues for 'Coverage.value'
        raise RuntimeError("Cannot reverse this migration. 'Coverage.value' and its values cannot be restored.")
        
        # The following code is provided here to aid in writing a correct migration        # Adding field 'Coverage.value'
        db.add_column(u'hs_core_coverage', 'value',
                      self.gf('django.db.models.fields.CharField')(max_length=200),
                      keep_default=False)

        # Deleting field 'Coverage._value'
        db.delete_column(u'hs_core_coverage', '_value')

        # Adding field 'GenericResource.metadata'
        db.add_column(u'hs_core_genericresource', 'metadata',
                      self.gf('django.db.models.fields.related.OneToOneField')(to=orm['hs_core.CoreMetaData'], unique=True, null=True, blank=True),
                      keep_default=False)

        # Deleting field 'GenericResource.object_id'
        db.delete_column(u'hs_core_genericresource', 'object_id')

        # Deleting field 'GenericResource.content_type'
        db.delete_column(u'hs_core_genericresource', 'content_type_id')


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
        u'hs_core.bags': {
            'Meta': {'ordering': "['-timestamp']", 'object_name': 'Bags'},
            'bag': ('django.db.models.fields.files.FileField', [], {'max_length': '100', 'null': 'True'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'db_index': 'True'})
        },
        u'hs_core.contributor': {
            'Meta': {'object_name': 'Contributor'},
            'address': ('django.db.models.fields.CharField', [], {'max_length': '250', 'null': 'True', 'blank': 'True'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            'description': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'null': 'True', 'blank': 'True'}),
            'homepage': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'organization': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'phone': ('django.db.models.fields.CharField', [], {'max_length': '25', 'null': 'True', 'blank': 'True'}),
            'researchGateID': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'researcherID': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'})
        },
        u'hs_core.coremetadata': {
            'Meta': {'object_name': 'CoreMetaData'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        u'hs_core.coverage': {
            'Meta': {'object_name': 'Coverage'},
            '_value': ('django.db.models.fields.CharField', [], {'max_length': '1024'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '20'})
        },
        u'hs_core.creator': {
            'Meta': {'ordering': "['order']", 'object_name': 'Creator'},
            'address': ('django.db.models.fields.CharField', [], {'max_length': '250', 'null': 'True', 'blank': 'True'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            'description': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'null': 'True', 'blank': 'True'}),
            'homepage': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'order': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'organization': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'phone': ('django.db.models.fields.CharField', [], {'max_length': '25', 'null': 'True', 'blank': 'True'}),
            'researchGateID': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'researcherID': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'})
        },
        u'hs_core.date': {
            'Meta': {'object_name': 'Date'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            'end_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'start_date': ('django.db.models.fields.DateTimeField', [], {}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '20'})
        },
        u'hs_core.description': {
            'Meta': {'unique_together': "(('content_type', 'object_id'),)", 'object_name': 'Description'},
            'abstract': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {})
        },
        u'hs_core.externalprofilelink': {
            'Meta': {'unique_together': "(('type', 'url', 'content_type'),)", 'object_name': 'ExternalProfileLink'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200'})
        },
        u'hs_core.format': {
            'Meta': {'object_name': 'Format'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'hs_core.genericresource': {
            'Meta': {'ordering': "(u'_order',)", 'object_name': 'GenericResource', '_ormbases': [u'pages.Page']},
            u'comments_count': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'content': ('mezzanine.core.fields.RichTextField', [], {}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']", 'null': 'True', 'blank': 'True'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'creator_of_hs_core_genericresource'", 'to': u"orm['auth.User']"}),
            'discoverable': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'do_not_distribute': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'doi': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '1024', 'null': 'True', 'blank': 'True'}),
            'edit_groups': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "u'group_editable_hs_core_genericresource'", 'null': 'True', 'symmetrical': 'False', 'to': u"orm['auth.Group']"}),
            'edit_users': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "u'user_editable_hs_core_genericresource'", 'null': 'True', 'symmetrical': 'False', 'to': u"orm['auth.User']"}),
            'frozen': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_changed_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'last_changed_hs_core_genericresource'", 'null': 'True', 'to': u"orm['auth.User']"}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'owners': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "u'owns_hs_core_genericresource'", 'symmetrical': 'False', 'to': u"orm['auth.User']"}),
            u'page_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['pages.Page']", 'unique': 'True', 'primary_key': 'True'}),
            'public': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'published_and_frozen': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'short_id': ('django.db.models.fields.CharField', [], {'default': "'431a704959e64f1fb228fa13b2ca0e8b'", 'max_length': '32', 'db_index': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'genericresources'", 'to': u"orm['auth.User']"}),
            'view_groups': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "u'group_viewable_hs_core_genericresource'", 'null': 'True', 'symmetrical': 'False', 'to': u"orm['auth.Group']"}),
            'view_users': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "u'user_viewable_hs_core_genericresource'", 'null': 'True', 'symmetrical': 'False', 'to': u"orm['auth.User']"})
        },
        u'hs_core.groupownership': {
            'Meta': {'object_name': 'GroupOwnership'},
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.Group']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"})
        },
        u'hs_core.identifier': {
            'Meta': {'object_name': 'Identifier'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'url': ('django.db.models.fields.URLField', [], {'unique': 'True', 'max_length': '200'})
        },
        u'hs_core.language': {
            'Meta': {'object_name': 'Language'},
            'code': ('django.db.models.fields.CharField', [], {'max_length': '3'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {})
        },
        u'hs_core.publisher': {
            'Meta': {'unique_together': "(('content_type', 'object_id'),)", 'object_name': 'Publisher'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200'})
        },
        u'hs_core.relation': {
            'Meta': {'object_name': 'Relation'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '500'})
        },
        u'hs_core.resourcefile': {
            'Meta': {'object_name': 'ResourceFile'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'resource_file': ('django.db.models.fields.files.FileField', [], {'max_length': '100'})
        },
        u'hs_core.rights': {
            'Meta': {'unique_together': "(('content_type', 'object_id'),)", 'object_name': 'Rights'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'statement': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'})
        },
        u'hs_core.source': {
            'Meta': {'object_name': 'Source'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            'derived_from': ('django.db.models.fields.CharField', [], {'max_length': '300'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {})
        },
        u'hs_core.subject': {
            'Meta': {'object_name': 'Subject'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'hs_core.title': {
            'Meta': {'unique_together': "(('content_type', 'object_id'),)", 'object_name': 'Title'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '300'})
        },
        u'hs_core.type': {
            'Meta': {'unique_together': "(('content_type', 'object_id'),)", 'object_name': 'Type'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200'})
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

    complete_apps = ['hs_core']