# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hs_file_types', '0003_auto_20170131_1736'),
        ('hs_core', '0032_auto_20170120_1445'),
    ]

    operations = [
        migrations.AddField(
            model_name='resourcefile',
            name='logical_file_new',
            field=models.ForeignKey(related_name='files', blank=True, to='hs_file_types.BaseLogicalFile', null=True),
        ),
    ]
