# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hs_access_control', '0017_auto_20161213_2029'),
    ]

    operations = [
        migrations.AddField(
            model_name='groupresourceprovenance',
            name='undone',
            field=models.BooleanField(default=False, editable=False),
        ),
        migrations.AddField(
            model_name='usergroupprovenance',
            name='undone',
            field=models.BooleanField(default=False, editable=False),
        ),
        migrations.AddField(
            model_name='userresourceprovenance',
            name='undone',
            field=models.BooleanField(default=False, editable=False),
        ),
        migrations.AlterField(
            model_name='groupresourceprovenance',
            name='state',
            field=models.IntegerField(default=1, editable=False, choices=[(1, b'Requested'), (2, b'Restored'), (3, b'Initial')]),
        ),
        migrations.AlterField(
            model_name='usergroupprovenance',
            name='state',
            field=models.IntegerField(default=1, editable=False, choices=[(1, b'Requested'), (2, b'Restored'), (3, b'Initial')]),
        ),
        migrations.AlterField(
            model_name='userresourceprovenance',
            name='state',
            field=models.IntegerField(default=1, editable=False, choices=[(1, b'Requested'), (2, b'Restored'), (3, b'Initial')]),
        ),
    ]
