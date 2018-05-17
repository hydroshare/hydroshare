# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hs_core', '0037_resourcefile_reference_file_size'),
    ]

    operations = [
        migrations.AddField(
            model_name='baseresource',
            name='minid',
            field=models.CharField(help_text=b'MINID created for this resource.', max_length=1024, null=True, db_index=True, blank=True),
        ),
    ]
