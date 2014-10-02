# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Party'
        db.create_table(u'hs_party_party', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uniqueCode', self.gf('django.db.models.fields.CharField')(default='dee17e4f-e35e-498d-b9f5-04b1553e5107', max_length=64)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length='255')),
            ('url', self.gf('django.db.models.fields.URLField')(max_length='255', blank=True)),
            ('notes', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('createdDate', self.gf('django.db.models.fields.DateField')(auto_now_add=True, blank=True)),
            ('lastUpdate', self.gf('django.db.models.fields.DateField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal('hs_party', ['Party'])

        # Adding model 'AddressCodeList'
        db.create_table(u'hs_party_addresscodelist', (
            ('code', self.gf('django.db.models.fields.CharField')(max_length=24, primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('order', self.gf('django.db.models.fields.IntegerField')(blank=True)),
            ('url', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
        ))
        db.send_create_signal('hs_party', ['AddressCodeList'])

        # Adding model 'PhoneCodeList'
        db.create_table(u'hs_party_phonecodelist', (
            ('code', self.gf('django.db.models.fields.CharField')(max_length=24, primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('order', self.gf('django.db.models.fields.IntegerField')(blank=True)),
            ('url', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
        ))
        db.send_create_signal('hs_party', ['PhoneCodeList'])

        # Adding model 'EmailCodeList'
        db.create_table(u'hs_party_emailcodelist', (
            ('code', self.gf('django.db.models.fields.CharField')(max_length=24, primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('order', self.gf('django.db.models.fields.IntegerField')(blank=True)),
            ('url', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
        ))
        db.send_create_signal('hs_party', ['EmailCodeList'])

        # Adding model 'City'
        db.create_table(u'hs_party_city', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('geonamesUrl', self.gf('django.db.models.fields.URLField')(max_length=200)),
        ))
        db.send_create_signal('hs_party', ['City'])

        # Adding model 'Region'
        db.create_table(u'hs_party_region', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('geonamesUrl', self.gf('django.db.models.fields.URLField')(max_length=200)),
        ))
        db.send_create_signal('hs_party', ['Region'])

        # Adding model 'Country'
        db.create_table(u'hs_party_country', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('geonamesUrl', self.gf('django.db.models.fields.URLField')(max_length=200)),
        ))
        db.send_create_signal('hs_party', ['Country'])

        # Adding model 'ExternalIdentifierCodeList'
        db.create_table(u'hs_party_externalidentifiercodelist', (
            ('code', self.gf('django.db.models.fields.CharField')(max_length=24, primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('order', self.gf('django.db.models.fields.IntegerField')(blank=True)),
            ('url', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
        ))
        db.send_create_signal('hs_party', ['ExternalIdentifierCodeList'])

        # Adding model 'NameAliasCodeList'
        db.create_table(u'hs_party_namealiascodelist', (
            ('code', self.gf('django.db.models.fields.CharField')(max_length=24, primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('order', self.gf('django.db.models.fields.IntegerField')(blank=True)),
            ('url', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
        ))
        db.send_create_signal('hs_party', ['NameAliasCodeList'])

        # Adding model 'Person'
        db.create_table(u'hs_party_person', (
            (u'party_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['hs_party.Party'], unique=True, primary_key=True)),
            (u'keywords_string', self.gf('django.db.models.fields.CharField')(max_length=500, blank=True)),
            ('site', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['sites.Site'])),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=500)),
            ('slug', self.gf('django.db.models.fields.CharField')(max_length=2000, null=True, blank=True)),
            ('_meta_title', self.gf('django.db.models.fields.CharField')(max_length=500, null=True, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('gen_description', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(null=True)),
            ('updated', self.gf('django.db.models.fields.DateTimeField')(null=True)),
            ('status', self.gf('django.db.models.fields.IntegerField')(default=2)),
            ('publish_date', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('expiry_date', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('short_url', self.gf('django.db.models.fields.URLField')(max_length=200, null=True, blank=True)),
            ('in_sitemap', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('givenName', self.gf('django.db.models.fields.CharField')(max_length='125')),
            ('familyName', self.gf('django.db.models.fields.CharField')(max_length='125')),
            ('jobTitle', self.gf('django.db.models.fields.CharField')(max_length='100', blank=True)),
            ('primaryOrganizationRecord', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='+', null=True, to=orm['hs_party.Organization'])),
        ))
        db.send_create_signal('hs_party', ['Person'])

        # Adding model 'PersonEmail'
        db.create_table(u'hs_party_personemail', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('email', self.gf('django.db.models.fields.CharField')(max_length='30', blank=True)),
            ('email_type', self.gf('django.db.models.fields.related.ForeignKey')(default='other', to=orm['hs_party.EmailCodeList'], blank=True)),
            ('person', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='email_addresses', null=True, to=orm['hs_party.Person'])),
        ))
        db.send_create_signal('hs_party', ['PersonEmail'])

        # Adding model 'PersonLocation'
        db.create_table(u'hs_party_personlocation', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('address', self.gf('django.db.models.fields.TextField')()),
            ('address_type', self.gf('django.db.models.fields.related.ForeignKey')(default='mailing', to=orm['hs_party.AddressCodeList'])),
            ('person', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='mail_addresses', null=True, to=orm['hs_party.Person'])),
        ))
        db.send_create_signal('hs_party', ['PersonLocation'])

        # Adding model 'PersonPhone'
        db.create_table(u'hs_party_personphone', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('phone_number', self.gf('django.db.models.fields.CharField')(max_length='30')),
            ('phone_type', self.gf('django.db.models.fields.related.ForeignKey')(default='other', to=orm['hs_party.PhoneCodeList'], blank=True)),
            ('person', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='phone_numbers', null=True, to=orm['hs_party.Person'])),
        ))
        db.send_create_signal('hs_party', ['PersonPhone'])

        # Adding model 'PersonExternalIdentifier'
        db.create_table(u'hs_party_personexternalidentifier', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('person', self.gf('django.db.models.fields.related.ForeignKey')(related_name='externalIdentifiers', to=orm['hs_party.Person'])),
            ('identifierName', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['hs_party.ExternalIdentifierCodeList'], max_length='10')),
            ('otherName', self.gf('django.db.models.fields.CharField')(max_length='255', blank=True)),
            ('identifierCode', self.gf('django.db.models.fields.CharField')(max_length='255')),
            ('createdDate', self.gf('django.db.models.fields.DateField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('hs_party', ['PersonExternalIdentifier'])

        # Adding model 'UserCodeList'
        db.create_table(u'hs_party_usercodelist', (
            ('code', self.gf('django.db.models.fields.CharField')(max_length=24, primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('order', self.gf('django.db.models.fields.IntegerField')(blank=True)),
            ('url', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
        ))
        db.send_create_signal('hs_party', ['UserCodeList'])

        # Adding model 'OtherName'
        db.create_table(u'hs_party_othername', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('otherName', self.gf('django.db.models.fields.CharField')(max_length='255')),
            ('annotation', self.gf('django.db.models.fields.related.ForeignKey')(default=700, to=orm['hs_party.NameAliasCodeList'], max_length='10')),
            ('persons', self.gf('django.db.models.fields.related.ForeignKey')(related_name='otherNames', to=orm['hs_party.Person'])),
        ))
        db.send_create_signal('hs_party', ['OtherName'])

        # Adding model 'OrganizationCodeList'
        db.create_table(u'hs_party_organizationcodelist', (
            ('code', self.gf('django.db.models.fields.CharField')(max_length=24, primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('order', self.gf('django.db.models.fields.IntegerField')(blank=True)),
            ('url', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
        ))
        db.send_create_signal('hs_party', ['OrganizationCodeList'])

        # Adding model 'Organization'
        db.create_table(u'hs_party_organization', (
            (u'party_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['hs_party.Party'], unique=True, primary_key=True)),
            (u'specialities_string', self.gf('django.db.models.fields.CharField')(max_length=500, blank=True)),
            (u'keywords_string', self.gf('django.db.models.fields.CharField')(max_length=500, blank=True)),
            ('site', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['sites.Site'])),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=500)),
            ('slug', self.gf('django.db.models.fields.CharField')(max_length=2000, null=True, blank=True)),
            ('_meta_title', self.gf('django.db.models.fields.CharField')(max_length=500, null=True, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('gen_description', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(null=True)),
            ('updated', self.gf('django.db.models.fields.DateTimeField')(null=True)),
            ('status', self.gf('django.db.models.fields.IntegerField')(default=2)),
            ('publish_date', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('expiry_date', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('short_url', self.gf('django.db.models.fields.URLField')(max_length=200, null=True, blank=True)),
            ('in_sitemap', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('logoUrl', self.gf('django.db.models.fields.files.ImageField')(max_length=100, blank=True)),
            ('parentOrganization', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['hs_party.Organization'], null=True, blank=True)),
            ('organizationType', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['hs_party.OrganizationCodeList'])),
        ))
        db.send_create_signal('hs_party', ['Organization'])

        # Adding model 'OrganizationEmail'
        db.create_table(u'hs_party_organizationemail', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('email', self.gf('django.db.models.fields.CharField')(max_length='30', blank=True)),
            ('email_type', self.gf('django.db.models.fields.related.ForeignKey')(default='other', to=orm['hs_party.EmailCodeList'], blank=True)),
            ('organization', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='email_addresses', null=True, to=orm['hs_party.Organization'])),
        ))
        db.send_create_signal('hs_party', ['OrganizationEmail'])

        # Adding model 'OrganizationLocation'
        db.create_table(u'hs_party_organizationlocation', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('address', self.gf('django.db.models.fields.TextField')()),
            ('address_type', self.gf('django.db.models.fields.related.ForeignKey')(default='mailing', to=orm['hs_party.AddressCodeList'])),
            ('organization', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='mail_addresses', null=True, to=orm['hs_party.Organization'])),
        ))
        db.send_create_signal('hs_party', ['OrganizationLocation'])

        # Adding model 'OrganizationPhone'
        db.create_table(u'hs_party_organizationphone', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('phone_number', self.gf('django.db.models.fields.CharField')(max_length='30')),
            ('phone_type', self.gf('django.db.models.fields.related.ForeignKey')(default='other', to=orm['hs_party.PhoneCodeList'], blank=True)),
            ('organization', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='phone_numbers', null=True, to=orm['hs_party.Organization'])),
        ))
        db.send_create_signal('hs_party', ['OrganizationPhone'])

        # Adding model 'OrganizationName'
        db.create_table(u'hs_party_organizationname', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('otherName', self.gf('django.db.models.fields.CharField')(max_length='255')),
            ('annotation', self.gf('django.db.models.fields.related.ForeignKey')(default=700, to=orm['hs_party.NameAliasCodeList'], max_length='10')),
            ('organization', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='alternate_names', null=True, to=orm['hs_party.Organization'])),
        ))
        db.send_create_signal('hs_party', ['OrganizationName'])

        # Adding model 'ExternalOrgIdentifier'
        db.create_table(u'hs_party_externalorgidentifier', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('organization', self.gf('django.db.models.fields.related.ForeignKey')(related_name='externalIdentifiers', to=orm['hs_party.Organization'])),
            ('identifierName', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['hs_party.ExternalIdentifierCodeList'], max_length='10')),
            ('otherName', self.gf('django.db.models.fields.CharField')(max_length='255', blank=True)),
            ('identifierCode', self.gf('django.db.models.fields.CharField')(max_length='255')),
            ('createdDate', self.gf('django.db.models.fields.DateField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('hs_party', ['ExternalOrgIdentifier'])

        # Adding model 'Group'
        db.create_table(u'hs_party_group', (
            (u'party_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['hs_party.Party'], unique=True, primary_key=True)),
            (u'keywords_string', self.gf('django.db.models.fields.CharField')(max_length=500, blank=True)),
            ('site', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['sites.Site'])),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=500)),
            ('slug', self.gf('django.db.models.fields.CharField')(max_length=2000, null=True, blank=True)),
            ('_meta_title', self.gf('django.db.models.fields.CharField')(max_length=500, null=True, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('gen_description', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(null=True)),
            ('updated', self.gf('django.db.models.fields.DateTimeField')(null=True)),
            ('status', self.gf('django.db.models.fields.IntegerField')(default=2)),
            ('publish_date', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('expiry_date', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('short_url', self.gf('django.db.models.fields.URLField')(max_length=200, null=True, blank=True)),
            ('in_sitemap', self.gf('django.db.models.fields.BooleanField')(default=True)),
        ))
        db.send_create_signal('hs_party', ['Group'])

        # Adding model 'OrganizationAssociation'
        db.create_table(u'hs_party_organizationassociation', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('createdDate', self.gf('django.db.models.fields.DateField')(auto_now_add=True, blank=True)),
            ('uniqueCode', self.gf('django.db.models.fields.CharField')(default='5233b8ca-139d-4eb0-bc6c-c48403cb9b57', max_length=64)),
            ('organization', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['hs_party.Organization'])),
            ('person', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['hs_party.Person'])),
            ('beginDate', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
            ('endDate', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
            ('jobTitle', self.gf('django.db.models.fields.CharField')(max_length='100', blank=True)),
            ('presentOrganization', self.gf('django.db.models.fields.BooleanField')(default=True)),
        ))
        db.send_create_signal('hs_party', ['OrganizationAssociation'])

        # Adding model 'ChoiceType'
        db.create_table(u'hs_party_choicetype', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('choiceType', self.gf('django.db.models.fields.CharField')(max_length=40)),
            ('code', self.gf('django.db.models.fields.CharField')(max_length=24)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('order', self.gf('django.db.models.fields.IntegerField')(blank=True)),
            ('url', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
        ))
        db.send_create_signal('hs_party', ['ChoiceType'])


    def backwards(self, orm):
        # Deleting model 'Party'
        db.delete_table(u'hs_party_party')

        # Deleting model 'AddressCodeList'
        db.delete_table(u'hs_party_addresscodelist')

        # Deleting model 'PhoneCodeList'
        db.delete_table(u'hs_party_phonecodelist')

        # Deleting model 'EmailCodeList'
        db.delete_table(u'hs_party_emailcodelist')

        # Deleting model 'City'
        db.delete_table(u'hs_party_city')

        # Deleting model 'Region'
        db.delete_table(u'hs_party_region')

        # Deleting model 'Country'
        db.delete_table(u'hs_party_country')

        # Deleting model 'ExternalIdentifierCodeList'
        db.delete_table(u'hs_party_externalidentifiercodelist')

        # Deleting model 'NameAliasCodeList'
        db.delete_table(u'hs_party_namealiascodelist')

        # Deleting model 'Person'
        db.delete_table(u'hs_party_person')

        # Deleting model 'PersonEmail'
        db.delete_table(u'hs_party_personemail')

        # Deleting model 'PersonLocation'
        db.delete_table(u'hs_party_personlocation')

        # Deleting model 'PersonPhone'
        db.delete_table(u'hs_party_personphone')

        # Deleting model 'PersonExternalIdentifier'
        db.delete_table(u'hs_party_personexternalidentifier')

        # Deleting model 'UserCodeList'
        db.delete_table(u'hs_party_usercodelist')

        # Deleting model 'OtherName'
        db.delete_table(u'hs_party_othername')

        # Deleting model 'OrganizationCodeList'
        db.delete_table(u'hs_party_organizationcodelist')

        # Deleting model 'Organization'
        db.delete_table(u'hs_party_organization')

        # Deleting model 'OrganizationEmail'
        db.delete_table(u'hs_party_organizationemail')

        # Deleting model 'OrganizationLocation'
        db.delete_table(u'hs_party_organizationlocation')

        # Deleting model 'OrganizationPhone'
        db.delete_table(u'hs_party_organizationphone')

        # Deleting model 'OrganizationName'
        db.delete_table(u'hs_party_organizationname')

        # Deleting model 'ExternalOrgIdentifier'
        db.delete_table(u'hs_party_externalorgidentifier')

        # Deleting model 'Group'
        db.delete_table(u'hs_party_group')

        # Deleting model 'OrganizationAssociation'
        db.delete_table(u'hs_party_organizationassociation')

        # Deleting model 'ChoiceType'
        db.delete_table(u'hs_party_choicetype')


    models = {
        'hs_party.addresscodelist': {
            'Meta': {'object_name': 'AddressCodeList'},
            'code': ('django.db.models.fields.CharField', [], {'max_length': '24', 'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'order': ('django.db.models.fields.IntegerField', [], {'blank': 'True'}),
            'url': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'})
        },
        'hs_party.choicetype': {
            'Meta': {'object_name': 'ChoiceType'},
            'choiceType': ('django.db.models.fields.CharField', [], {'max_length': '40'}),
            'code': ('django.db.models.fields.CharField', [], {'max_length': '24'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'order': ('django.db.models.fields.IntegerField', [], {'blank': 'True'}),
            'url': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'})
        },
        'hs_party.city': {
            'Meta': {'object_name': 'City'},
            'geonamesUrl': ('django.db.models.fields.URLField', [], {'max_length': '200'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'hs_party.country': {
            'Meta': {'object_name': 'Country'},
            'geonamesUrl': ('django.db.models.fields.URLField', [], {'max_length': '200'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'hs_party.emailcodelist': {
            'Meta': {'object_name': 'EmailCodeList'},
            'code': ('django.db.models.fields.CharField', [], {'max_length': '24', 'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'order': ('django.db.models.fields.IntegerField', [], {'blank': 'True'}),
            'url': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'})
        },
        'hs_party.externalidentifiercodelist': {
            'Meta': {'object_name': 'ExternalIdentifierCodeList'},
            'code': ('django.db.models.fields.CharField', [], {'max_length': '24', 'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'order': ('django.db.models.fields.IntegerField', [], {'blank': 'True'}),
            'url': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'})
        },
        'hs_party.externalorgidentifier': {
            'Meta': {'object_name': 'ExternalOrgIdentifier'},
            'createdDate': ('django.db.models.fields.DateField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'identifierCode': ('django.db.models.fields.CharField', [], {'max_length': "'255'"}),
            'identifierName': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['hs_party.ExternalIdentifierCodeList']", 'max_length': "'10'"}),
            'organization': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'externalIdentifiers'", 'to': "orm['hs_party.Organization']"}),
            'otherName': ('django.db.models.fields.CharField', [], {'max_length': "'255'", 'blank': 'True'})
        },
        'hs_party.group': {
            'Meta': {'object_name': 'Group', '_ormbases': ['hs_party.Party']},
            '_meta_title': ('django.db.models.fields.CharField', [], {'max_length': '500', 'null': 'True', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'expiry_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'gen_description': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'in_sitemap': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            u'keywords_string': ('django.db.models.fields.CharField', [], {'max_length': '500', 'blank': 'True'}),
            u'party_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['hs_party.Party']", 'unique': 'True', 'primary_key': 'True'}),
            'publish_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'short_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'site': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['sites.Site']"}),
            'slug': ('django.db.models.fields.CharField', [], {'max_length': '2000', 'null': 'True', 'blank': 'True'}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '2'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'null': 'True'})
        },
        'hs_party.namealiascodelist': {
            'Meta': {'object_name': 'NameAliasCodeList'},
            'code': ('django.db.models.fields.CharField', [], {'max_length': '24', 'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'order': ('django.db.models.fields.IntegerField', [], {'blank': 'True'}),
            'url': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'})
        },
        'hs_party.organization': {
            'Meta': {'object_name': 'Organization', '_ormbases': ['hs_party.Party']},
            '_meta_title': ('django.db.models.fields.CharField', [], {'max_length': '500', 'null': 'True', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'expiry_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'gen_description': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'in_sitemap': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            u'keywords_string': ('django.db.models.fields.CharField', [], {'max_length': '500', 'blank': 'True'}),
            'logoUrl': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'blank': 'True'}),
            'organizationType': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['hs_party.OrganizationCodeList']"}),
            'parentOrganization': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['hs_party.Organization']", 'null': 'True', 'blank': 'True'}),
            u'party_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['hs_party.Party']", 'unique': 'True', 'primary_key': 'True'}),
            'persons': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'organizations'", 'to': "orm['hs_party.Person']", 'through': "orm['hs_party.OrganizationAssociation']", 'blank': 'True', 'symmetrical': 'False', 'null': 'True'}),
            'publish_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'short_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'site': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['sites.Site']"}),
            'slug': ('django.db.models.fields.CharField', [], {'max_length': '2000', 'null': 'True', 'blank': 'True'}),
            u'specialities_string': ('django.db.models.fields.CharField', [], {'max_length': '500', 'blank': 'True'}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '2'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'null': 'True'})
        },
        'hs_party.organizationassociation': {
            'Meta': {'object_name': 'OrganizationAssociation'},
            'beginDate': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'createdDate': ('django.db.models.fields.DateField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'endDate': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'jobTitle': ('django.db.models.fields.CharField', [], {'max_length': "'100'", 'blank': 'True'}),
            'organization': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['hs_party.Organization']"}),
            'person': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['hs_party.Person']"}),
            'presentOrganization': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'uniqueCode': ('django.db.models.fields.CharField', [], {'default': "'36ca4dd0-8dd2-450a-a084-dc42d88437be'", 'max_length': '64'})
        },
        'hs_party.organizationcodelist': {
            'Meta': {'object_name': 'OrganizationCodeList'},
            'code': ('django.db.models.fields.CharField', [], {'max_length': '24', 'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'order': ('django.db.models.fields.IntegerField', [], {'blank': 'True'}),
            'url': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'})
        },
        'hs_party.organizationemail': {
            'Meta': {'object_name': 'OrganizationEmail'},
            'email': ('django.db.models.fields.CharField', [], {'max_length': "'30'", 'blank': 'True'}),
            'email_type': ('django.db.models.fields.related.ForeignKey', [], {'default': "'other'", 'to': "orm['hs_party.EmailCodeList']", 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'organization': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'email_addresses'", 'null': 'True', 'to': "orm['hs_party.Organization']"})
        },
        'hs_party.organizationlocation': {
            'Meta': {'object_name': 'OrganizationLocation'},
            'address': ('django.db.models.fields.TextField', [], {}),
            'address_type': ('django.db.models.fields.related.ForeignKey', [], {'default': "'mailing'", 'to': "orm['hs_party.AddressCodeList']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'organization': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'mail_addresses'", 'null': 'True', 'to': "orm['hs_party.Organization']"})
        },
        'hs_party.organizationname': {
            'Meta': {'object_name': 'OrganizationName'},
            'annotation': ('django.db.models.fields.related.ForeignKey', [], {'default': '700', 'to': "orm['hs_party.NameAliasCodeList']", 'max_length': "'10'"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'organization': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'alternate_names'", 'null': 'True', 'to': "orm['hs_party.Organization']"}),
            'otherName': ('django.db.models.fields.CharField', [], {'max_length': "'255'"})
        },
        'hs_party.organizationphone': {
            'Meta': {'object_name': 'OrganizationPhone'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'organization': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'phone_numbers'", 'null': 'True', 'to': "orm['hs_party.Organization']"}),
            'phone_number': ('django.db.models.fields.CharField', [], {'max_length': "'30'"}),
            'phone_type': ('django.db.models.fields.related.ForeignKey', [], {'default': "'other'", 'to': "orm['hs_party.PhoneCodeList']", 'blank': 'True'})
        },
        'hs_party.othername': {
            'Meta': {'object_name': 'OtherName'},
            'annotation': ('django.db.models.fields.related.ForeignKey', [], {'default': '700', 'to': "orm['hs_party.NameAliasCodeList']", 'max_length': "'10'"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'otherName': ('django.db.models.fields.CharField', [], {'max_length': "'255'"}),
            'persons': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'otherNames'", 'to': "orm['hs_party.Person']"})
        },
        'hs_party.party': {
            'Meta': {'object_name': 'Party'},
            'createdDate': ('django.db.models.fields.DateField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lastUpdate': ('django.db.models.fields.DateField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': "'255'"}),
            'notes': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'uniqueCode': ('django.db.models.fields.CharField', [], {'default': "'8e8bdd79-05cb-444d-ad4e-bb7716dadb16'", 'max_length': '64'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': "'255'", 'blank': 'True'})
        },
        'hs_party.person': {
            'Meta': {'object_name': 'Person', '_ormbases': ['hs_party.Party']},
            '_meta_title': ('django.db.models.fields.CharField', [], {'max_length': '500', 'null': 'True', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'expiry_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'familyName': ('django.db.models.fields.CharField', [], {'max_length': "'125'"}),
            'gen_description': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'givenName': ('django.db.models.fields.CharField', [], {'max_length': "'125'"}),
            'in_sitemap': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'jobTitle': ('django.db.models.fields.CharField', [], {'max_length': "'100'", 'blank': 'True'}),
            u'keywords_string': ('django.db.models.fields.CharField', [], {'max_length': '500', 'blank': 'True'}),
            u'party_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['hs_party.Party']", 'unique': 'True', 'primary_key': 'True'}),
            'primaryOrganizationRecord': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': "orm['hs_party.Organization']"}),
            'publish_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'short_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'site': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['sites.Site']"}),
            'slug': ('django.db.models.fields.CharField', [], {'max_length': '2000', 'null': 'True', 'blank': 'True'}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '2'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'null': 'True'})
        },
        'hs_party.personemail': {
            'Meta': {'object_name': 'PersonEmail'},
            'email': ('django.db.models.fields.CharField', [], {'max_length': "'30'", 'blank': 'True'}),
            'email_type': ('django.db.models.fields.related.ForeignKey', [], {'default': "'other'", 'to': "orm['hs_party.EmailCodeList']", 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'person': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'email_addresses'", 'null': 'True', 'to': "orm['hs_party.Person']"})
        },
        'hs_party.personexternalidentifier': {
            'Meta': {'object_name': 'PersonExternalIdentifier'},
            'createdDate': ('django.db.models.fields.DateField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'identifierCode': ('django.db.models.fields.CharField', [], {'max_length': "'255'"}),
            'identifierName': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['hs_party.ExternalIdentifierCodeList']", 'max_length': "'10'"}),
            'otherName': ('django.db.models.fields.CharField', [], {'max_length': "'255'", 'blank': 'True'}),
            'person': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'externalIdentifiers'", 'to': "orm['hs_party.Person']"})
        },
        'hs_party.personlocation': {
            'Meta': {'object_name': 'PersonLocation'},
            'address': ('django.db.models.fields.TextField', [], {}),
            'address_type': ('django.db.models.fields.related.ForeignKey', [], {'default': "'mailing'", 'to': "orm['hs_party.AddressCodeList']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'person': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'mail_addresses'", 'null': 'True', 'to': "orm['hs_party.Person']"})
        },
        'hs_party.personphone': {
            'Meta': {'object_name': 'PersonPhone'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'person': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'phone_numbers'", 'null': 'True', 'to': "orm['hs_party.Person']"}),
            'phone_number': ('django.db.models.fields.CharField', [], {'max_length': "'30'"}),
            'phone_type': ('django.db.models.fields.related.ForeignKey', [], {'default': "'other'", 'to': "orm['hs_party.PhoneCodeList']", 'blank': 'True'})
        },
        'hs_party.phonecodelist': {
            'Meta': {'object_name': 'PhoneCodeList'},
            'code': ('django.db.models.fields.CharField', [], {'max_length': '24', 'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'order': ('django.db.models.fields.IntegerField', [], {'blank': 'True'}),
            'url': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'})
        },
        'hs_party.region': {
            'Meta': {'object_name': 'Region'},
            'geonamesUrl': ('django.db.models.fields.URLField', [], {'max_length': '200'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'hs_party.usercodelist': {
            'Meta': {'object_name': 'UserCodeList'},
            'code': ('django.db.models.fields.CharField', [], {'max_length': '24', 'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'order': ('django.db.models.fields.IntegerField', [], {'blank': 'True'}),
            'url': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'})
        },
        u'sites.site': {
            'Meta': {'ordering': "(u'domain',)", 'object_name': 'Site', 'db_table': "u'django_site'"},
            'domain': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        }
    }

    complete_apps = ['hs_party']