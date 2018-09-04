# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hs_explore', '0015_auto_20180723_2242'),
    ]

    operations = [
        migrations.AddField(
            model_name='recommendedresource',
            name='rec_type',
            field=models.CharField(max_length=10, null=True, choices=[(b'Ownership', b'Ownership'), (b'Propensity', b'Propensity')]),
        ),
    ]
