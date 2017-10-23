# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hs_tools_resource', '0012_toolmetadata_approved'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='toolmetadata',
            options={'verbose_name': 'Application Approval', 'verbose_name_plural': 'Application Approvals'},
        ),
    ]
