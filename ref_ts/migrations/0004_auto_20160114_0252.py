# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hs_access_control', '0005_remove_useraccess_active'),
        ('hs_core', '0014_auto_20151123_1451'),
        ('hs_labels', '0002_custom_migration'),
        ('contenttypes', '0001_initial'),
        ('ref_ts', '0003_reftimeseries'),
    ]

    operations = [
        migrations.CreateModel(
            name='DataSource',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('code', models.CharField(default=b'', max_length=500, blank=True)),
                ('content_type', models.ForeignKey(related_name='ref_ts_datasource_related', to='contenttypes.ContentType')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.RemoveField(
            model_name='reftimeseries',
            name='baseresource_ptr',
        ),
        migrations.DeleteModel(
            name='RefTimeSeries',
        ),
        migrations.CreateModel(
            name='RefTimeSeriesResource',
            fields=[
            ],
            options={
                'ordering': ('_order',),
                'verbose_name': 'HIS Referenced Time Series',
                'proxy': True,
            },
            bases=('hs_core.baseresource',),
        ),
        migrations.RemoveField(
            model_name='method',
            name='value',
        ),
        migrations.RemoveField(
            model_name='qualitycontrollevel',
            name='value',
        ),
        migrations.AddField(
            model_name='method',
            name='code',
            field=models.CharField(default=b'', max_length=500, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='method',
            name='description',
            field=models.TextField(default=b'', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='qualitycontrollevel',
            name='code',
            field=models.CharField(default=b'', max_length=500, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='qualitycontrollevel',
            name='definition',
            field=models.CharField(default=b'', max_length=500, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='site',
            name='net_work',
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
            name='latitude',
            field=models.DecimalField(null=True, max_digits=9, decimal_places=6, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='site',
            name='longitude',
            field=models.DecimalField(null=True, max_digits=9, decimal_places=6, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='site',
            name='name',
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
