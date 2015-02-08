# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hs_core', '0002_auto_20150127_1847'),
    ]

    operations = [
        migrations.AlterField(
            model_name='relation',
            name='type',
            field=models.CharField(max_length=100, choices=[(b'isPartOf', b'Part Of'), (b'isExecutedBy', b'Executed By'), (b'isCreatedBy', b'Created By'), (b'isVersionOf', b'Version Of'), (b'isDataFor', b'Data For'), (b'cites', b'Cites')]),
            preserve_default=True,
        ),
    ]
