# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hs_core', '0013_auto_20151114_2314'),
    ]

    operations = [
        migrations.AlterField(
            model_name='relation',
            name='type',
            field=models.CharField(max_length=100, choices=[(b'isHostedBy', b'Hosted By'), (b'isCopiedFrom', b'Copied From'), (b'isPartOf', b'Part Of'), (b'isExecutedBy', b'Executed By'), (b'isCreatedBy', b'Created By'), (b'isVersionOf', b'Version Of'), (b'isDataFor', b'Data For'), (b'cites', b'Cites')]),
            preserve_default=True,
        ),
    ]
