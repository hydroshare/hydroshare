# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hs_explore', '0018_auto_20180724_1638'),
    ]

    operations = [
        migrations.AlterField(
            model_name='recommendedresource',
            name='rec_type',
            field=models.CharField(max_length=11, null=True, choices=[(b'Ownership', b'Ownership'), (b'Propensity', b'Propensity'), (b'Combination', b'Combination')]),
        ),
    ]
