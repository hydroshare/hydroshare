# -*- coding: utf-8 -*-
# Generated by Django 1.11.28 on 2020-06-03 21:10
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hs_access_control', '0025_auto_20190924_1622'),
    ]

    operations = [
        migrations.AlterField(
            model_name='feature',
            name='feature',
            field=models.IntegerField(choices=[(0, 'None'), (1, 'CZO')], default=0),
        ),
    ]
