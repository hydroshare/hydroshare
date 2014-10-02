# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'SiteConfiguration'
        db.create_table(u'theme_siteconfiguration', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('site', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['sites.Site'])),
            ('col1_heading', self.gf('django.db.models.fields.CharField')(default='Contact us', max_length=200)),
            ('col1_content', self.gf('mezzanine.core.fields.RichTextField')()),
            ('col2_heading', self.gf('django.db.models.fields.CharField')(default='Go social', max_length=200)),
            ('col2_content', self.gf('mezzanine.core.fields.RichTextField')(blank=True)),
            ('col3_heading', self.gf('django.db.models.fields.CharField')(default='Subscribe', max_length=200)),
            ('col3_content', self.gf('mezzanine.core.fields.RichTextField')()),
            ('twitter_link', self.gf('django.db.models.fields.CharField')(max_length=2000, blank=True)),
            ('facebook_link', self.gf('django.db.models.fields.CharField')(max_length=2000, blank=True)),
            ('pinterest_link', self.gf('django.db.models.fields.CharField')(max_length=2000, blank=True)),
            ('youtube_link', self.gf('django.db.models.fields.CharField')(max_length=2000, blank=True)),
            ('github_link', self.gf('django.db.models.fields.CharField')(max_length=2000, blank=True)),
            ('linkedin_link', self.gf('django.db.models.fields.CharField')(max_length=2000, blank=True)),
            ('vk_link', self.gf('django.db.models.fields.CharField')(max_length=2000, blank=True)),
            ('gplus_link', self.gf('django.db.models.fields.CharField')(max_length=2000, blank=True)),
            ('has_social_network_links', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('copyright', self.gf('django.db.models.fields.TextField')(default='&copy {% now "Y" %} {{ settings.SITE_TITLE }}')),
        ))
        db.send_create_signal(u'theme', ['SiteConfiguration'])

        # Adding model 'HomePage'
        db.create_table(u'theme_homepage', (
            (u'page_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['pages.Page'], unique=True, primary_key=True)),
            ('heading', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('slide_in_one_icon', self.gf('django.db.models.fields.CharField')(max_length=50, blank=True)),
            ('slide_in_one', self.gf('django.db.models.fields.CharField')(max_length=200, blank=True)),
            ('slide_in_two_icon', self.gf('django.db.models.fields.CharField')(max_length=50, blank=True)),
            ('slide_in_two', self.gf('django.db.models.fields.CharField')(max_length=200, blank=True)),
            ('slide_in_three_icon', self.gf('django.db.models.fields.CharField')(max_length=50, blank=True)),
            ('slide_in_three', self.gf('django.db.models.fields.CharField')(max_length=200, blank=True)),
            ('header_background', self.gf('mezzanine.core.fields.FileField')(max_length=255, blank=True)),
            ('header_image', self.gf('mezzanine.core.fields.FileField')(max_length=255, null=True, blank=True)),
            ('welcome_heading', self.gf('django.db.models.fields.CharField')(default='Welcome', max_length=100)),
            ('content', self.gf('mezzanine.core.fields.RichTextField')()),
            ('recent_blog_heading', self.gf('django.db.models.fields.CharField')(default='Latest blog posts', max_length=100)),
            ('number_recent_posts', self.gf('django.db.models.fields.PositiveIntegerField')(default=3)),
        ))
        db.send_create_signal(u'theme', ['HomePage'])

        # Adding model 'IconBox'
        db.create_table(u'theme_iconbox', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('_order', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('homepage', self.gf('django.db.models.fields.related.ForeignKey')(related_name='boxes', to=orm['theme.HomePage'])),
            ('icon', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('link_text', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('link', self.gf('django.db.models.fields.CharField')(max_length=2000, blank=True)),
        ))
        db.send_create_signal(u'theme', ['IconBox'])


    def backwards(self, orm):
        # Deleting model 'SiteConfiguration'
        db.delete_table(u'theme_siteconfiguration')

        # Deleting model 'HomePage'
        db.delete_table(u'theme_homepage')

        # Deleting model 'IconBox'
        db.delete_table(u'theme_iconbox')


    models = {
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
        },
        u'theme.homepage': {
            'Meta': {'ordering': "(u'_order',)", 'object_name': 'HomePage', '_ormbases': [u'pages.Page']},
            'content': ('mezzanine.core.fields.RichTextField', [], {}),
            'header_background': ('mezzanine.core.fields.FileField', [], {'max_length': '255', 'blank': 'True'}),
            'header_image': ('mezzanine.core.fields.FileField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'heading': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'number_recent_posts': ('django.db.models.fields.PositiveIntegerField', [], {'default': '3'}),
            u'page_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['pages.Page']", 'unique': 'True', 'primary_key': 'True'}),
            'recent_blog_heading': ('django.db.models.fields.CharField', [], {'default': "'Latest blog posts'", 'max_length': '100'}),
            'slide_in_one': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'slide_in_one_icon': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'slide_in_three': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'slide_in_three_icon': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'slide_in_two': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'slide_in_two_icon': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'welcome_heading': ('django.db.models.fields.CharField', [], {'default': "'Welcome'", 'max_length': '100'})
        },
        u'theme.iconbox': {
            'Meta': {'ordering': "(u'_order',)", 'object_name': 'IconBox'},
            '_order': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'homepage': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'boxes'", 'to': u"orm['theme.HomePage']"}),
            'icon': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'link': ('django.db.models.fields.CharField', [], {'max_length': '2000', 'blank': 'True'}),
            'link_text': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        u'theme.siteconfiguration': {
            'Meta': {'object_name': 'SiteConfiguration'},
            'col1_content': ('mezzanine.core.fields.RichTextField', [], {}),
            'col1_heading': ('django.db.models.fields.CharField', [], {'default': "'Contact us'", 'max_length': '200'}),
            'col2_content': ('mezzanine.core.fields.RichTextField', [], {'blank': 'True'}),
            'col2_heading': ('django.db.models.fields.CharField', [], {'default': "'Go social'", 'max_length': '200'}),
            'col3_content': ('mezzanine.core.fields.RichTextField', [], {}),
            'col3_heading': ('django.db.models.fields.CharField', [], {'default': "'Subscribe'", 'max_length': '200'}),
            'copyright': ('django.db.models.fields.TextField', [], {'default': '\'&copy {% now "Y" %} {{ settings.SITE_TITLE }}\''}),
            'facebook_link': ('django.db.models.fields.CharField', [], {'max_length': '2000', 'blank': 'True'}),
            'github_link': ('django.db.models.fields.CharField', [], {'max_length': '2000', 'blank': 'True'}),
            'gplus_link': ('django.db.models.fields.CharField', [], {'max_length': '2000', 'blank': 'True'}),
            'has_social_network_links': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'linkedin_link': ('django.db.models.fields.CharField', [], {'max_length': '2000', 'blank': 'True'}),
            'pinterest_link': ('django.db.models.fields.CharField', [], {'max_length': '2000', 'blank': 'True'}),
            'site': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['sites.Site']"}),
            'twitter_link': ('django.db.models.fields.CharField', [], {'max_length': '2000', 'blank': 'True'}),
            'vk_link': ('django.db.models.fields.CharField', [], {'max_length': '2000', 'blank': 'True'}),
            'youtube_link': ('django.db.models.fields.CharField', [], {'max_length': '2000', 'blank': 'True'})
        }
    }

    complete_apps = ['theme']