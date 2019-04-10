# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hs_dictionary', '0002_auto_20170824_1900'),
    ]

    operations = [
        migrations.CreateModel(
            name='UncategorizedTerm',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255)),
            ],
            options={
                'verbose_name_plural': 'uncategorized terms',
            },
        ),
        migrations.AlterModelOptions(
            name='university',
            options={'verbose_name_plural': 'universities'},
        ),
    ]
