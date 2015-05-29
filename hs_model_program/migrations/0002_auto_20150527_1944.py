# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hs_model_program', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='mpmetadata',
            name='date_released',
            field=models.DateTimeField(help_text=b'The date of the software release (m/d/Y H:M)', null=True, verbose_name=b'Release Date', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='mpmetadata',
            name='operating_sys',
            field=models.CharField(default=b'', max_length=255, blank=True, help_text=b'Compatible operating systems', null=True, verbose_name=b'Operating System'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='mpmetadata',
            name='program_website',
            field=models.CharField(default=b'', max_length=255, blank=True, help_text=b'A URL providing addition information about the software', null=True, verbose_name=b'Website'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='mpmetadata',
            name='software_repo',
            field=models.CharField(default=b'', max_length=255, blank=True, help_text=b'A URL for the source code repository (e.g. git, mecurial, svn)', null=True, verbose_name=b'Software Repository'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='mpmetadata',
            name='software_version',
            field=models.CharField(default=b'', max_length=255, blank=True, help_text=b'The software version of the model', null=True, verbose_name=b'Version '),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='mpmetadata',
            name='source_code',
            field=models.CharField(default=b'', choices=[(b'-', b'    ')], max_length=400, blank=True, help_text=b'Archive of the  source code for the model (e.g. .zip, .tar)', null=True, verbose_name=b'Source Code'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='mpmetadata',
            name='theoretical_manual',
            field=models.CharField(default=b'', choices=[(b'-', b'    ')], max_length=400, blank=True, help_text=b'Theoretical manual for the model program (e.g. .doc, .md, .rtf, .pdf', null=True, verbose_name=b'Theoretical Manual'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='mpmetadata',
            name='user_manual',
            field=models.CharField(default=b'', choices=[(b'-', b'    ')], max_length=400, blank=True, help_text=b'User manual for the model program (e.g. .doc, .md, .rtf, .pdf', null=True, verbose_name=b'User Manual'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='mpmetadata',
            unique_together=set([('content_type', 'object_id')]),
        ),
    ]
