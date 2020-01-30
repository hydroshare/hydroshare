# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hs_model_program', '0004_auto_20151012_1656'),
    ]

    operations = [
        migrations.AddField(
            model_name='mpmetadata',
            name='modelEngine',
            field=models.CharField(default='', max_length=400, blank=True, help_text='Uploaded archive containing model software (source code, executable, etc.)', null=True, verbose_name='Computational Engine'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='mpmetadata',
            name='modelCodeRepository',
            field=models.CharField(default='', max_length=255, blank=True, help_text='A URL to the source code repository (e.g. git, mercurial, svn)', null=True, verbose_name='Software Repository'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='mpmetadata',
            name='modelDocumentation',
            field=models.CharField(default='', max_length=400, blank=True, help_text='Documentation for the model (e.g. User manuals, theoretical manuals, reports, notes, etc.)', null=True, verbose_name='Documentation'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='mpmetadata',
            name='modelProgramLanguage',
            field=models.CharField(default='', max_length=100, blank=True, help_text='The programming language(s) that the model is written in', null=True, verbose_name='Language'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='mpmetadata',
            name='modelReleaseNotes',
            field=models.CharField(default='', max_length=400, blank=True, help_text='Notes regarding the software release (e.g. bug fixes, new functionality, readme)', null=True, verbose_name='Release Notes'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='mpmetadata',
            name='modelSoftware',
            field=models.CharField(default='', max_length=400, blank=True, help_text='Uploaded archive containing model software (e.g., utilities software, etc.)', null=True, verbose_name='Software'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='mpmetadata',
            name='modelVersion',
            field=models.CharField(default='', max_length=255, blank=True, help_text='The software version or build number of the model', null=True, verbose_name='Version'),
            preserve_default=True,
        ),
    ]
