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
            name='ModelProgramMetaData',
            fields=[
                ('coremetadata_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='hs_core.CoreMetaData')),
            ],
            options={
            },
            bases=('hs_core.coremetadata',),
        ),
        migrations.CreateModel(
            name='ModelProgramResource',
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
                ('creator', models.ForeignKey(related_name='creator_of_hs_model_program_modelprogramresource', to=settings.AUTH_USER_MODEL, help_text=b'This is the person who first uploaded the resource')),
                ('edit_groups', models.ManyToManyField(help_text=b'This is the set of xDCIShare Groups who can edit the resource', related_name='group_editable_hs_model_program_modelprogramresource', null=True, to=b'auth.Group', blank=True)),
                ('edit_users', models.ManyToManyField(help_text=b'This is the set of xDCIShare Users who can edit the resource', related_name='user_editable_hs_model_program_modelprogramresource', null=True, to=settings.AUTH_USER_MODEL, blank=True)),
                ('last_changed_by', models.ForeignKey(related_name='last_changed_hs_model_program_modelprogramresource', to=settings.AUTH_USER_MODEL, help_text=b'The person who last changed the resource', null=True)),
                ('owners', models.ManyToManyField(help_text=b'The person who has total ownership of the resource', related_name='owns_hs_model_program_modelprogramresource', to=settings.AUTH_USER_MODEL)),
                ('user', models.ForeignKey(related_name='modelprogramresources', verbose_name='Author', to=settings.AUTH_USER_MODEL)),
                ('view_groups', models.ManyToManyField(help_text=b'This is the set of xDCIShare Groups who can view the resource', related_name='group_viewable_hs_model_program_modelprogramresource', null=True, to=b'auth.Group', blank=True)),
                ('view_users', models.ManyToManyField(help_text=b'This is the set of xDCIShare Users who can view the resource', related_name='user_viewable_hs_model_program_modelprogramresource', null=True, to=settings.AUTH_USER_MODEL, blank=True)),
            ],
            options={
                'ordering': ('_order',),
                'verbose_name': 'Model Program Resource',
            },
            bases=('pages.page', models.Model),
        ),
        migrations.CreateModel(
            name='MpMetadata',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('software_version', models.CharField(default=b'', max_length=255, blank=True, help_text=b'The software version of the model', null=True, verbose_name=b'Version ')),
                ('software_language', models.CharField(default=b'', max_length=100, blank=True, help_text=b'The programming language(s) that the model was written in', null=True, verbose_name=b'Language')),
                ('operating_sys', models.CharField(default=b'', max_length=255, blank=True, help_text=b'Compatible operating systems', null=True, verbose_name=b'Operating System')),
                ('date_released', models.DateTimeField(help_text=b'The date of the software release (m/d/Y H:M)', null=True, verbose_name=b'Release Date', blank=True)),
                ('program_website', models.CharField(default=b'', max_length=255, blank=True, help_text=b'A URL providing addition information about the software', null=True, verbose_name=b'Website')),
                ('software_repo', models.CharField(default=b'', max_length=255, blank=True, help_text=b'A URL for the source code repository (e.g. git, mecurial, svn)', null=True, verbose_name=b'Software Repository')),
                ('release_notes', models.CharField(default=b'', choices=[(b'-', b'    ')], max_length=400, blank=True, help_text=b'Notes about the software release (e.g. bug fixes, new functionality)', null=True, verbose_name=b'Release Notes')),
                ('user_manual', models.CharField(default=b'', choices=[(b'-', b'    ')], max_length=400, blank=True, help_text=b'User manual for the model program (e.g. .doc, .md, .rtf, .pdf', null=True, verbose_name=b'User Manual')),
                ('theoretical_manual', models.CharField(default=b'', choices=[(b'-', b'    ')], max_length=400, blank=True, help_text=b'Theoretical manual for the model program (e.g. .doc, .md, .rtf, .pdf', null=True, verbose_name=b'Theoretical Manual')),
                ('source_code', models.CharField(default=b'', choices=[(b'-', b'    ')], max_length=400, blank=True, help_text=b'Archive of the  source code for the model (e.g. .zip, .tar)', null=True, verbose_name=b'Source Code')),
                ('content_type', models.ForeignKey(related_name='hs_model_program_mpmetadata_related', to='contenttypes.ContentType')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='mpmetadata',
            unique_together=set([('content_type', 'object_id')]),
        ),
    ]
