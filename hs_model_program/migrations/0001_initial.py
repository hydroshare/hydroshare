# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('hs_core', '__first__'),
    ]

    operations = [
        migrations.CreateModel(
            name='ModelProgramMetaData',
            fields=[
                ('coremetadata_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='hs_core.CoreMetaData')),
            ],
            bases=('hs_core.coremetadata',),
        ),
        migrations.CreateModel(
            name='MpMetadata',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('modelVersion', models.CharField(default=b'', max_length=255, blank=True, help_text=b'The software version or build number of the model', null=True, verbose_name=b'Version')),
                ('modelProgramLanguage', models.CharField(default=b'', max_length=100, blank=True, help_text=b'The programming language(s) that the model is written in', null=True, verbose_name=b'Language')),
                ('modelOperatingSystem', models.CharField(default=b'', max_length=255, blank=True, help_text=b'Compatible operating systems to setup and run the model', null=True, verbose_name=b'Operating System')),
                ('modelReleaseDate', models.DateTimeField(help_text=b'The date that this version of the model was released', null=True, verbose_name=b'Release Date', blank=True)),
                ('modelWebsite', models.CharField(default=b'', max_length=255, blank=True, help_text=b'A URL to the website maintained by the model developers', null=True, verbose_name=b'Website')),
                ('modelCodeRepository', models.CharField(default=b'', max_length=255, blank=True, help_text=b'A URL to the source code repository (e.g. git, mercurial, svn)', null=True, verbose_name=b'Software Repository')),
                ('modelReleaseNotes', models.CharField(default=b'', max_length=400, blank=True, help_text=b'Notes regarding the software release (e.g. bug fixes, new functionality, readme)', null=True, verbose_name=b'Release Notes')),
                ('modelDocumentation', models.CharField(default=b'', max_length=400, blank=True, help_text=b'Documentation for the model (e.g. User manuals, theoretical manuals, reports, notes, etc.)', null=True, verbose_name=b'Documentation')),
                ('modelSoftware', models.CharField(default=b'', max_length=400, blank=True, help_text=b'Uploaded archive containing model software (e.g., utilities software, etc.)', null=True, verbose_name=b'Software')),
                ('modelEngine', models.CharField(default=b'', max_length=400, blank=True, help_text=b'Uploaded archive containing model software (source code, executable, etc.)', null=True, verbose_name=b'Computational Engine')),
                ('content_type', models.ForeignKey(related_name='hs_model_program_mpmetadata_related', to='contenttypes.ContentType')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ModelProgramResource',
            fields=[
            ],
            options={
                'ordering': ('_order',),
                'verbose_name': 'Model Program Resource',
                'proxy': True,
            },
            bases=('hs_core.baseresource',),
        ),
    ]
