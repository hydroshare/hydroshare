# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('theme', '0006_auto_20170309_1516'),
    ]

    operations = [
        migrations.AddField(
            model_name='homepage',
            name='message_end_date',
            field=models.DateField(help_text=b'Date on which the message will no more be displayed', null=True),
        ),
        migrations.AddField(
            model_name='homepage',
            name='message_start_date',
            field=models.DateField(help_text=b'Date from which the message will be displayed', null=True),
        ),
        migrations.AddField(
            model_name='homepage',
            name='message_type',
            field=models.CharField(default=b'Information', max_length=100, choices=[(b'warning', b'Warning'), (b'information', b'Information')]),
        ),
        migrations.AddField(
            model_name='homepage',
            name='show_message',
            field=models.BooleanField(default=False, help_text=b'Check to show message'),
        ),
    ]
