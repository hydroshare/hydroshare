# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hs_explore', '0009_auto_20180702_0445'),
    ]

    operations = [
        migrations.AddField(
            model_name='grouppreftopair',
            name='weight',
            field=models.FloatField(default=1.0, editable=False),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='userpreftopair',
            name='weight',
            field=models.FloatField(default=1.0, editable=False),
            preserve_default=False,
        ),
    ]
