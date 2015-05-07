# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('hs_tools_resource', '0002_auto_20150324_0300'),
    ]

    operations = [
        migrations.AlterField(
            model_name='toolresource',
            name='owners',
            field=models.ManyToManyField(help_text=b'The person who has total ownership of the resource', related_name='owns_hs_tools_resource_toolresource', to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='toolresourcetype',
            name='tool_res_type',
            field=models.CharField(max_length=b'500', null=True),
            preserve_default=True,
        ),
    ]
