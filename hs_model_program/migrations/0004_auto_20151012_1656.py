# -*- coding: utf-8 -*-


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
            field=models.CharField(default='', max_length=255, blank=True, help_text='A URL to the source code repository (e.g. git, mecurial, svn)', null=True, verbose_name='Software Repository'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='mpmetadata',
            name='modelDocumentation',
            field=models.CharField(default='', choices=[('-', '    ')], max_length=400, blank=True, help_text='Documentation for the model (e.g. User manuals, theoretical manuals, reports, notes, etc.)', null=True, verbose_name='Model Documentation'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='mpmetadata',
            name='modelOperatingSystem',
            field=models.CharField(default='', max_length=255, blank=True, help_text='Compatible operating systems to setup and run the model', null=True, verbose_name='Operating System'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='mpmetadata',
            name='modelProgramLanguage',
            field=models.CharField(default='', max_length=100, blank=True, help_text='The programming language(s) that the model is written in', null=True, verbose_name='Program Language'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='mpmetadata',
            name='modelReleaseDate',
            field=models.DateTimeField(help_text='The date that this version of the model was released', null=True, verbose_name='Release Date', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='mpmetadata',
            name='modelReleaseNotes',
            field=models.CharField(default='', choices=[('-', '    ')], max_length=400, blank=True, help_text='Notes regarding the software release (e.g. bug fixes, new functionality, readme)', null=True, verbose_name='Release Notes'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='mpmetadata',
            name='modelSoftware',
            field=models.CharField(default='', choices=[('-', '    ')], max_length=400, blank=True, help_text='Uploaded archive containing model software (source code, executable, etc.)', null=True, verbose_name='Model Software'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='mpmetadata',
            name='modelVersion',
            field=models.CharField(default='', max_length=255, blank=True, help_text='The software version or build number of the model', null=True, verbose_name='Version '),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='mpmetadata',
            name='modelWebsite',
            field=models.CharField(default='', max_length=255, blank=True, help_text='A URL to the website maintained by the model developers', null=True, verbose_name='Website'),
            preserve_default=True,
        ),
    ]
