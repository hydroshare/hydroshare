# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('hs_access_control', '0018_auto_20170112_1604'),
    ]

    operations = [
        migrations.AlterField(
            model_name='usergroupprovenance',
            name='grantor',
            field=models.ForeignKey(related_name='x2ugq', editable=False, to=settings.AUTH_USER_MODEL, help_text=b'grantor of privilege', null=True),
        ),
    ]
