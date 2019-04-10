# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hs_tools_resource', '0011_toolicon_data_url'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='supportedrestypes',
            unique_together=set([('content_type', 'object_id')]),
        ),
        migrations.AlterUniqueTogether(
            name='supportedsharingstatus',
            unique_together=set([('content_type', 'object_id')]),
        ),
    ]
