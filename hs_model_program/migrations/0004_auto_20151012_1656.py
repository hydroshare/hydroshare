# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hs_model_program', '0003_auto_20150813_1730'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='mpmetadata',
            name='date_released',
        ),
        migrations.RemoveField(
            model_name='mpmetadata',
            name='operating_sys',
        ),
        migrations.RemoveField(
            model_name='mpmetadata',
            name='program_website',
        ),
        migrations.RemoveField(
            model_name='mpmetadata',
            name='release_notes',
        ),
        migrations.RemoveField(
            model_name='mpmetadata',
            name='software_language',
        ),
        migrations.RemoveField(
            model_name='mpmetadata',
            name='software_repo',
        ),
        migrations.RemoveField(
            model_name='mpmetadata',
            name='software_version',
        ),
        migrations.RemoveField(
            model_name='mpmetadata',
            name='source_code',
        ),
        migrations.RemoveField(
            model_name='mpmetadata',
            name='theoretical_manual',
        ),
        migrations.RemoveField(
            model_name='mpmetadata',
            name='user_manual',
        ),
        migrations.AddField(
            model_name='mpmetadata',
            name='modelCodeRepository',
            field=models.CharField(default=b'', max_length=255, blank=True, help_text=b'A URL to the source code repository (e.g. git, mecurial, svn)', null=True, verbose_name=b'Software Repository'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='mpmetadata',
            name='modelDocumentation',
            field=models.CharField(default=b'', choices=[(b'-', b'    ')], max_length=400, blank=True, help_text=b'Documentation for the model (e.g. User manuals, theoretical manuals, reports, notes, etc.)', null=True, verbose_name=b'Model Documentation'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='mpmetadata',
            name='modelOperatingSystem',
            field=models.CharField(default=b'', max_length=255, blank=True, help_text=b'Compatible operating systems to setup and run the model', null=True, verbose_name=b'Operating System'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='mpmetadata',
            name='modelProgramLanguage',
            field=models.CharField(default=b'', max_length=100, blank=True, help_text=b'The programming language(s) that the model is written in', null=True, verbose_name=b'Program Language'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='mpmetadata',
            name='modelReleaseDate',
            field=models.DateTimeField(help_text=b'The date that this version of the model was released', null=True, verbose_name=b'Release Date', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='mpmetadata',
            name='modelReleaseNotes',
            field=models.CharField(default=b'', choices=[(b'-', b'    ')], max_length=400, blank=True, help_text=b'Notes regarding the software release (e.g. bug fixes, new functionality, readme)', null=True, verbose_name=b'Release Notes'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='mpmetadata',
            name='modelSoftware',
            field=models.CharField(default=b'', choices=[(b'-', b'    ')], max_length=400, blank=True, help_text=b'Uploaded archive containing model software (source code, executable, etc.)', null=True, verbose_name=b'Model Software'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='mpmetadata',
            name='modelVersion',
            field=models.CharField(default=b'', max_length=255, blank=True, help_text=b'The software version or build number of the model', null=True, verbose_name=b'Version '),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='mpmetadata',
            name='modelWebsite',
            field=models.CharField(default=b'', max_length=255, blank=True, help_text=b'A URL to the website maintained by the model developers', null=True, verbose_name=b'Website'),
            preserve_default=True,
        ),
    ]
