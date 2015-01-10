# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('hs_model_program', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='hydroprogramresource',
            name='software_rights',
            field=models.TextField(default=b'', help_text=b'The software rights of the program (e.g. http://creativecommons.org/licenses/by/4.0)', verbose_name=b'Software Rights'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='hydroprogramresource',
            name='date_released',
            field=models.DateTimeField(default=datetime.datetime(2015, 1, 9, 23, 47, 6, 110867), help_text=b'The date of the software release (mm/dd/yyyy hh:mm)', null=True, verbose_name=b'Date of Software Release'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='hydroprogramresource',
            name='theoretical_manual',
            field=models.FileField(default=None, upload_to=b'./hs/hydromodel', null=True, verbose_name=b'Theoretical Manual', help_text=b'Theoretical manual for the model program (e.g. .doc, .md, .rtf, .pdf'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='hydroprogramresource',
            name='user_manual',
            field=models.FileField(default=None, upload_to=b'./hs/hydromodel', null=True, verbose_name=b'User Manual', help_text=b'User manual for the model program (e.g. .doc, .md, .rtf, .pdf'),
            preserve_default=True,
        ),
    ]
