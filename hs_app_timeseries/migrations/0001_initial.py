# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Method',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('method_code', models.IntegerField()),
                ('method_name', models.CharField(max_length=200)),
                ('method_type', models.CharField(max_length=200)),
                ('method_description', models.TextField(null=True, blank=True)),
                ('method_link', models.URLField(null=True, blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='ProcessingLevel',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('processing_level_code', models.IntegerField()),
                ('definition', models.CharField(max_length=200, null=True, blank=True)),
                ('explanation', models.TextField(null=True, blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='Site',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('site_code', models.CharField(max_length=200)),
                ('site_name', models.CharField(max_length=255)),
                ('elevation_m', models.IntegerField(null=True, blank=True)),
                ('elevation_datum', models.CharField(max_length=50, null=True, blank=True)),
                ('site_type', models.CharField(max_length=100, null=True, blank=True)),
            ],
        ),
    ]
