# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hs_explore', '0020_auto_20180729_0434'),
    ]

    operations = [
        migrations.AddField(
            model_name='grouppreftopair',
            name='state',
            field=models.CharField(default=b'Seen', max_length=8, choices=[(b'Seen', b'Seen'), (b'Rejected', b'Rejected')]),
        ),
    ]
