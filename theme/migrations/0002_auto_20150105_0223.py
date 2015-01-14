# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('theme', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='details',
            field=models.TextField(help_text=b'Tell the Hydroshare community a little about yourself.', null=True, verbose_name=b'Description', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='organization',
            field=models.CharField(help_text=b'The name of the organization you work for.', max_length=1024, null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='public',
            field=models.BooleanField(default=True, help_text=b'Uncheck to make your profile contact information and details private.'),
            preserve_default=True,
        ),
    ]
