# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hs_rhessys_inst_resource', '0005_auto_20150210_2233'),
    ]

    operations = [
        migrations.AddField(
            model_name='modelrun',
            name='status',
            field=models.CharField(blank=True, max_length=32, null=True, choices=[(b'Running', b'Running'), (b'Finished', b'Finished'), (b'Error', b'Error')]),
            preserve_default=True,
        ),
    ]
