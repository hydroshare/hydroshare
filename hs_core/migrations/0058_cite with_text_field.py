# -*- coding: utf-8 -*-
# Generated by Django 1.11.29 on 2021-11-29 18:20
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hs_core', '0057_auto_20210104_2106'),
    ]

    operations = [
        migrations.AlterField(
            model_name='relation',
            name='value',
            field=models.TextField(),
        ),
        migrations.AlterField(
            model_name='source',
            name='derived_from',
            field=models.TextField(),
        ),
    ]