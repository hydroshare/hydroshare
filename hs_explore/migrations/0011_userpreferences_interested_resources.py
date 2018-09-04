# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hs_core', '0037_auto_20180209_0309'),
        ('hs_explore', '0010_auto_20180702_1636'),
    ]

    operations = [
        migrations.AddField(
            model_name='userpreferences',
            name='interested_resources',
            field=models.ManyToManyField(related_name='interested_resources', editable=False, to='hs_core.BaseResource'),
        ),
    ]
