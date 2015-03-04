# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
import hs_core.models
import mezzanine.core.fields
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0001_initial'),
        ('pages', '__first__'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('contenttypes', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='HydroProgramResource',
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
                ('software_version', models.CharField(default=b'1.0', help_text=b'The software version of the model program', max_length=255, verbose_name=b'Software Version ', blank=True)),
                ('software_language', models.CharField(default=b'', help_text=b'The programming language that the model program was written in', max_length=100, verbose_name=b'Software Language')),
                ('operating_sys', models.CharField(default=b'unknown', help_text=b'Identify the operating system used by the model program', max_length=255, verbose_name=b'Operating System', blank=True)),
                ('date_released', models.DateTimeField(default=datetime.datetime(2015, 1, 9, 20, 0, 37, 772001), help_text=b'The date of the software release (mm/dd/yyyy hh:mm)', verbose_name=b'Date of Software Release')),
                ('release_notes', models.TextField(default=b'', help_text=b'Notes about the software release (e.g. bug fixes, new functionality)', verbose_name=b'Release Notes')),
                ('program_website', models.CharField(default=None, max_length=255, null=True, verbose_name=b'Model Website', help_text=b'A URL providing addition information about the software')),
                ('software_repo', models.CharField(default=None, max_length=255, null=True, verbose_name=b'Software Repository', help_text=b'A URL for the source code repository')),
                ('user_manual', models.FileField(default=None, help_text=b'User manual for the model program (e.g. .doc, .md, .rtf, .pdf', verbose_name=b'User Manual', upload_to=b'./hs/hydromodel')),
                ('theoretical_manual', models.FileField(default=None, help_text=b'Theoretical manual for the model program (e.g. .doc, .md, .rtf, .pdf', verbose_name=b'Theoretical Manual', upload_to=b'./hs/hydromodel')),
                ('source_code', models.FileField(default=None, help_text=b'Upload Model Source Code as *.ZIP', verbose_name=b'Model Source Code', upload_to=b'./hs/hydromodel')),
                ('exec_code', models.FileField(default=None, help_text=b'Upload Model Executables as *.ZIP', verbose_name=b'Model Executable Code', upload_to=b'./hs/hydromodel')),
                ('build_notes', models.TextField(default=b'', help_text=b'Notes about building/compiling the source code', verbose_name=b'Build Notes')),
                ('content_type', models.ForeignKey(blank=True, to='contenttypes.ContentType', null=True)),
                ('creator', models.ForeignKey(related_name='creator_of_hs_model_program_hydroprogramresource', to=settings.AUTH_USER_MODEL, help_text=b'This is the person who first uploaded the resource')),
                ('edit_groups', models.ManyToManyField(help_text=b'This is the set of Hydroshare Groups who can edit the resource', related_name='group_editable_hs_model_program_hydroprogramresource', null=True, to='auth.Group', blank=True)),
                ('edit_users', models.ManyToManyField(help_text=b'This is the set of Hydroshare Users who can edit the resource', related_name='user_editable_hs_model_program_hydroprogramresource', null=True, to=settings.AUTH_USER_MODEL, blank=True)),
                ('last_changed_by', models.ForeignKey(related_name='last_changed_hs_model_program_hydroprogramresource', to=settings.AUTH_USER_MODEL, help_text=b'The person who last changed the resource', null=True)),
                ('owners', models.ManyToManyField(help_text=b'The person who uploaded the resource', related_name='owns_hs_model_program_hydroprogramresource', to=settings.AUTH_USER_MODEL)),
                ('user', models.ForeignKey(related_name='hydroprogramresources', verbose_name='Author', to=settings.AUTH_USER_MODEL)),
                ('view_groups', models.ManyToManyField(help_text=b'This is the set of Hydroshare Groups who can view the resource', related_name='group_viewable_hs_model_program_hydroprogramresource', null=True, to='auth.Group', blank=True)),
                ('view_users', models.ManyToManyField(help_text=b'This is the set of Hydroshare Users who can view the resource', related_name='user_viewable_hs_model_program_hydroprogramresource', null=True, to=settings.AUTH_USER_MODEL, blank=True)),
            ],
            options={
                'ordering': ('_order',),
                'verbose_name': 'HydroProgram',
            },
            bases=('pages.page', models.Model),
        ),
    ]
