# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('hs_access_control', '0019_auto_20170112_1622'),
    ]

    operations = [
        migrations.AlterField(
            model_name='groupresourceprovenance',
            name='grantor',
            field=models.ForeignKey(related_name='x2grq', editable=False, to=settings.AUTH_USER_MODEL, help_text=b'grantor of privilege', null=True),
        ),
        migrations.AlterField(
            model_name='userresourceprovenance',
            name='grantor',
            field=models.ForeignKey(related_name='x2urq', editable=False, to=settings.AUTH_USER_MODEL, help_text=b'grantor of privilege', null=True),
        ),
    ]
