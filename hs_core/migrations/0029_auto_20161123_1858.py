# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hs_core', '0028_baseresource_extra_data'),
    ]

    operations = [
        migrations.AlterField(
            model_name='contributor',
            name='name',
            field=models.CharField(max_length=100, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='creator',
            name='name',
            field=models.CharField(max_length=100, null=True, blank=True),
        ),
    ]
