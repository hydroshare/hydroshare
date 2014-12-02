# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.contrib.gis.db.models.fields


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='OGRDataset',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('location', models.TextField()),
                ('checksum', models.CharField(max_length=32)),
                ('name', models.CharField(max_length=255, db_index=True)),
                ('human_name', models.TextField(db_index=True, null=True, blank=True)),
                ('extent', django.contrib.gis.db.models.fields.PolygonField(srid=4326)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='OGRDatasetCollection',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='OGRLayer',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255, db_index=True)),
                ('human_name', models.TextField(db_index=True, null=True, blank=True)),
                ('extent', django.contrib.gis.db.models.fields.PolygonField(srid=4326)),
                ('dataset', models.ForeignKey(to='ga_ows.OGRDataset')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='ogrdataset',
            name='collection',
            field=models.ForeignKey(to='ga_ows.OGRDatasetCollection'),
            preserve_default=True,
        ),
    ]
