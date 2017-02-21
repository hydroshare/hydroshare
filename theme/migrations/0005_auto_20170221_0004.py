# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('theme', '0004_userprofile_create_irods_user_account'),
    ]

    operations = [
        migrations.AddField(
            model_name='homepage',
            name='message_end_date',
            field=models.DateField(help_text=b'Date after which the message will no more be displayed', null=True),
        ),
        migrations.AddField(
            model_name='homepage',
            name='message_start_date',
            field=models.DateField(help_text=b'Date on which the message will be displayed', null=True),
        ),
    ]
