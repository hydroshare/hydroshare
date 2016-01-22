# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hs_tools_resource', '0004_auto_20151204_2301'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='requesturlbase',
            name='resShortID',
        ),
    ]
