# -*- coding: utf-8 -*-


from django.db import migrations, models
import django.contrib.postgres.fields
import django.contrib.postgres.fields.hstore


class Migration(migrations.Migration):

    dependencies = [
        ('hs_file_types', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='NetCDFFileMetaData',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('extra_metadata', django.contrib.postgres.fields.hstore.HStoreField(default={})),
                ('keywords', django.contrib.postgres.fields.ArrayField(default=[], base_field=models.CharField(max_length=100, null=True, blank=True), size=None)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='NetCDFLogicalFile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('dataset_name', models.CharField(max_length=255, null=True, blank=True)),
                ('metadata', models.OneToOneField(related_name='logical_file', on_delete=models.CASCADE, to='hs_file_types.NetCDFFileMetaData')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='genericfilemetadata',
            name='keywords',
            field=django.contrib.postgres.fields.ArrayField(default=[], base_field=models.CharField(max_length=100, null=True, blank=True), size=None),
        ),
        migrations.AddField(
            model_name='georasterfilemetadata',
            name='keywords',
            field=django.contrib.postgres.fields.ArrayField(default=[], base_field=models.CharField(max_length=100, null=True, blank=True), size=None),
        ),
    ]
