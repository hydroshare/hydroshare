# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hs_rhessys_inst_resource', '0010_modelrunoptions_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='modelrunoptions',
            name='value',
            field=models.CharField(default='', max_length=4096),
            preserve_default=False,
        ),
    ]
