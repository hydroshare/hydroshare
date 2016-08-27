# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.contrib.postgres.fields


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('hs_app_timeseries', '0009_timeseriesmetadata_value_counts'),
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
    ]
