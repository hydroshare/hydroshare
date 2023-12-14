# -*- coding: utf-8 -*-


from django.db import migrations, models
import django.contrib.postgres.fields
import django.contrib.postgres.fields.hstore


class Migration(migrations.Migration):

    dependencies = [
        ('hs_file_types', '0004_geofeaturefilemetadata_geofeaturelogicalfile'),
    ]

    operations = [
        migrations.CreateModel(
            name='RefTimeseriesFileMetaData',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('extra_metadata', django.contrib.postgres.fields.hstore.HStoreField(default={})),
                ('keywords', django.contrib.postgres.fields.ArrayField(default=[], base_field=models.CharField(max_length=100, null=True, blank=True), size=None)),
                ('is_dirty', models.BooleanField(default=False)),
                ('json_file_content', models.TextField()),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='RefTimeseriesLogicalFile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('dataset_name', models.CharField(max_length=255, null=True, blank=True)),
                ('metadata', models.OneToOneField(related_name='logical_file', on_delete=models.CASCADE, to='hs_file_types.RefTimeseriesFileMetaData')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
