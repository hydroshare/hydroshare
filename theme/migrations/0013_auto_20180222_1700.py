# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('theme', '0012_1_15_RC_merge'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='email_opt_out',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='siteconfiguration',
            name='copyright',
            field=models.TextField(default=b'&copy; {% now "Y" %} {{ settings.SITE_TITLE }}'),
        ),
    ]
