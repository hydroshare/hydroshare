# -*- coding: utf-8 -*-
# Generated by Django 1.11.29 on 2022-05-26 15:48
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ref_ts', '0004_auto_20160114_0252'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='datasource',
            name='content_type',
        ),
        migrations.RemoveField(
            model_name='method',
            name='content_type',
        ),
        migrations.RemoveField(
            model_name='qualitycontrollevel',
            name='content_type',
        ),
        migrations.RemoveField(
            model_name='referenceurl',
            name='content_type',
        ),
        migrations.RemoveField(
            model_name='reftsmetadata',
            name='coremetadata_ptr',
        ),
        migrations.RemoveField(
            model_name='site',
            name='content_type',
        ),
        migrations.RemoveField(
            model_name='variable',
            name='content_type',
        ),
        migrations.DeleteModel(
            name='RefTimeSeriesResource',
        ),
        migrations.DeleteModel(
            name='DataSource',
        ),
        migrations.DeleteModel(
            name='Method',
        ),
        migrations.DeleteModel(
            name='QualityControlLevel',
        ),
        migrations.DeleteModel(
            name='ReferenceURL',
        ),
        migrations.DeleteModel(
            name='RefTSMetadata',
        ),
        migrations.DeleteModel(
            name='Site',
        ),
        migrations.DeleteModel(
            name='Variable',
        ),
    ]