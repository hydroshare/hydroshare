# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ref_ts', '0004_auto_20160112_2116'),
    ]

    operations = [
        migrations.AlterField(
            model_name='datasource',
            name='code',
            field=models.CharField(default=b'', max_length=500, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='method',
            name='code',
            field=models.CharField(default=b'', max_length=500, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='method',
            name='description',
            field=models.TextField(default=b'', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='qualitycontrollevel',
            name='code',
            field=models.CharField(default=b'', max_length=500, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='qualitycontrollevel',
            name='definition',
            field=models.CharField(default=b'', max_length=500, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='site',
            name='code',
            field=models.CharField(default=b'', max_length=500, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='site',
            name='name',
            field=models.CharField(default=b'', max_length=500, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='site',
            name='net_work',
            field=models.CharField(default=b'', max_length=500, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='variable',
            name='code',
            field=models.CharField(default=b'', max_length=500, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='variable',
            name='data_type',
            field=models.CharField(default=b'', max_length=500, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='variable',
            name='name',
            field=models.CharField(default=b'', max_length=500, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='variable',
            name='sample_medium',
            field=models.CharField(default=b'', max_length=500, blank=True),
            preserve_default=True,
        ),
    ]
