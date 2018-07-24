# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hs_publication', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='publicationqueue',
            name='status',
            field=models.CharField(max_length=8, choices=[(b'pending', b'Pending Approval'), (b'approved', b'Publication Approved'), (b'denied', b'Publication Request Denied')]),
        ),
    ]
