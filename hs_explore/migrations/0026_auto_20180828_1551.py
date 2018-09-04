# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hs_explore', '0025_remove_grouppreftopair_state'),
    ]

    operations = [
        migrations.AlterField(
            model_name='grouppreferences',
            name='group',
            field=models.OneToOneField(editable=False, to='auth.Group'),
        ),
    ]
