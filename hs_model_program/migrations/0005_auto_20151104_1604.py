# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hs_model_program', '0004_auto_20151012_1656'),
    ]

    operations = [
        migrations.AddField(
            model_name='mpmetadata',
            name='modelEngine',
            field=models.CharField(default=b'', max_length=400, blank=True, help_text=b'Uploaded archive containing model software (source code, executable, etc.)', null=True, verbose_name=b'Computational Engine'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='mpmetadata',
            name='modelCodeRepository',
            field=models.CharField(default=b'', max_length=255, blank=True, help_text=b'A URL to the source code repository (e.g. git, mercurial, svn)', null=True, verbose_name=b'Software Repository'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='mpmetadata',
            name='modelDocumentation',
            field=models.CharField(default=b'', max_length=400, blank=True, help_text=b'Documentation for the model (e.g. User manuals, theoretical manuals, reports, notes, etc.)', null=True, verbose_name=b'Documentation'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='mpmetadata',
            name='modelProgramLanguage',
            field=models.CharField(default=b'', max_length=100, blank=True, help_text=b'The programming language(s) that the model is written in', null=True, verbose_name=b'Language'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='mpmetadata',
            name='modelReleaseNotes',
            field=models.CharField(default=b'', max_length=400, blank=True, help_text=b'Notes regarding the software release (e.g. bug fixes, new functionality, readme)', null=True, verbose_name=b'Release Notes'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='mpmetadata',
            name='modelSoftware',
            field=models.CharField(default=b'', max_length=400, blank=True, help_text=b'Uploaded archive containing model software (e.g., utilities software, etc.)', null=True, verbose_name=b'Software'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='mpmetadata',
            name='modelVersion',
            field=models.CharField(default=b'', max_length=255, blank=True, help_text=b'The software version or build number of the model', null=True, verbose_name=b'Version'),
            preserve_default=True,
        ),
    ]
