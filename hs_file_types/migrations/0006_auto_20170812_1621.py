# -*- coding: utf-8 -*-


from django.db import migrations, models
import django.contrib.postgres.fields
import django.contrib.postgres.fields.hstore


class Migration(migrations.Migration):

    dependencies = [
        ('hs_file_types', '0005_reftimeseriesfilemetadata_reftimeserieslogicalfile'),
    ]

    operations = [
        migrations.CreateModel(
            name='CVAggregationStatistic',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('term', models.CharField(max_length=255)),
                ('name', models.CharField(max_length=255)),
                ('is_dirty', models.BooleanField(default=False)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='CVElevationDatum',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('term', models.CharField(max_length=255)),
                ('name', models.CharField(max_length=255)),
                ('is_dirty', models.BooleanField(default=False)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='CVMedium',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('term', models.CharField(max_length=255)),
                ('name', models.CharField(max_length=255)),
                ('is_dirty', models.BooleanField(default=False)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='CVMethodType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('term', models.CharField(max_length=255)),
                ('name', models.CharField(max_length=255)),
                ('is_dirty', models.BooleanField(default=False)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='CVSiteType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('term', models.CharField(max_length=255)),
                ('name', models.CharField(max_length=255)),
                ('is_dirty', models.BooleanField(default=False)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='CVSpeciation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('term', models.CharField(max_length=255)),
                ('name', models.CharField(max_length=255)),
                ('is_dirty', models.BooleanField(default=False)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='CVStatus',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('term', models.CharField(max_length=255)),
                ('name', models.CharField(max_length=255)),
                ('is_dirty', models.BooleanField(default=False)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='CVUnitsType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('term', models.CharField(max_length=255)),
                ('name', models.CharField(max_length=255)),
                ('is_dirty', models.BooleanField(default=False)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='CVVariableName',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('term', models.CharField(max_length=255)),
                ('name', models.CharField(max_length=255)),
                ('is_dirty', models.BooleanField(default=False)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='CVVariableType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('term', models.CharField(max_length=255)),
                ('name', models.CharField(max_length=255)),
                ('is_dirty', models.BooleanField(default=False)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='TimeSeriesFileMetaData',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('value_counts', django.contrib.postgres.fields.hstore.HStoreField(default={})),
                ('extra_metadata', django.contrib.postgres.fields.hstore.HStoreField(default={})),
                ('keywords', django.contrib.postgres.fields.ArrayField(default=[], base_field=models.CharField(max_length=100, null=True, blank=True), size=None)),
                ('is_dirty', models.BooleanField(default=False)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='TimeSeriesLogicalFile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('dataset_name', models.CharField(max_length=255, null=True, blank=True)),
                ('metadata', models.OneToOneField(related_name='logical_file', on_delete=models.CASCADE, to='hs_file_types.TimeSeriesFileMetaData')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='cvvariabletype',
            name='metadata',
            field=models.ForeignKey(related_name='cv_variable_types', on_delete=models.CASCADE, to='hs_file_types.TimeSeriesFileMetaData'),
        ),
        migrations.AddField(
            model_name='cvvariablename',
            name='metadata',
            field=models.ForeignKey(related_name='cv_variable_names', on_delete=models.CASCADE, to='hs_file_types.TimeSeriesFileMetaData'),
        ),
        migrations.AddField(
            model_name='cvunitstype',
            name='metadata',
            field=models.ForeignKey(related_name='cv_units_types', on_delete=models.CASCADE, to='hs_file_types.TimeSeriesFileMetaData'),
        ),
        migrations.AddField(
            model_name='cvstatus',
            name='metadata',
            field=models.ForeignKey(related_name='cv_statuses', on_delete=models.CASCADE, to='hs_file_types.TimeSeriesFileMetaData'),
        ),
        migrations.AddField(
            model_name='cvspeciation',
            name='metadata',
            field=models.ForeignKey(related_name='cv_speciations', on_delete=models.CASCADE, to='hs_file_types.TimeSeriesFileMetaData'),
        ),
        migrations.AddField(
            model_name='cvsitetype',
            name='metadata',
            field=models.ForeignKey(related_name='cv_site_types', on_delete=models.CASCADE, to='hs_file_types.TimeSeriesFileMetaData'),
        ),
        migrations.AddField(
            model_name='cvmethodtype',
            name='metadata',
            field=models.ForeignKey(related_name='cv_method_types', on_delete=models.CASCADE, to='hs_file_types.TimeSeriesFileMetaData'),
        ),
        migrations.AddField(
            model_name='cvmedium',
            name='metadata',
            field=models.ForeignKey(related_name='cv_mediums', on_delete=models.CASCADE, to='hs_file_types.TimeSeriesFileMetaData'),
        ),
        migrations.AddField(
            model_name='cvelevationdatum',
            name='metadata',
            field=models.ForeignKey(related_name='cv_elevation_datums', on_delete=models.CASCADE, to='hs_file_types.TimeSeriesFileMetaData'),
        ),
        migrations.AddField(
            model_name='cvaggregationstatistic',
            name='metadata',
            field=models.ForeignKey(related_name='cv_aggregation_statistics', on_delete=models.CASCADE, to='hs_file_types.TimeSeriesFileMetaData'),
        ),
    ]
