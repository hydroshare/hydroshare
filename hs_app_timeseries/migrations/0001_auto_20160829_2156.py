# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.contrib.postgres.fields
import django.contrib.postgres.fields.hstore


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('hs_app_timeseries', 'custom_data_migration_20160718'),
    ]

    operations = [
        migrations.CreateModel(
            name='UTCOffSet',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('series_ids', django.contrib.postgres.fields.ArrayField(default=[], base_field=models.CharField(max_length=36, null=True, blank=True), size=None)),
                ('is_dirty', models.BooleanField(default=False)),
                ('value', models.FloatField(default=0.0)),
                ('content_type', models.ForeignKey(related_name='hs_app_timeseries_utcoffset_related', to='contenttypes.ContentType')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='site',
            name='latitude',
            field=models.FloatField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='site',
            name='longitude',
            field=models.FloatField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='timeseriesmetadata',
            name='value_counts',
            field=django.contrib.postgres.fields.hstore.HStoreField(default={}),
        ),
        migrations.AddField(
            model_name='timeseriesresult',
            name='series_label',
            field=models.CharField(max_length=255, null=True, blank=True),
        ),
    ]
