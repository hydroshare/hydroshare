# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hs_script_resource', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='scriptspecificmetadata',
            name='scriptCodeRepository',
            field=models.URLField(help_text=b'A URL to the source code repository (e.g. git, mercurial, svn)', max_length=255, verbose_name=b'Script Repository', blank=True),
        ),
    ]
