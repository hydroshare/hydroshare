# -*- coding: utf-8 -*-


from django.db import migrations, models
import django.contrib.postgres.fields
import django.contrib.postgres.fields.hstore


class Migration(migrations.Migration):

    dependencies = [
        ('hs_composite_resource', '0001_initial'),
        ('hs_file_types', '0008_auto_20180910_1731'),
    ]

    operations = [
        migrations.CreateModel(
            name='FileSetLogicalFile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('dataset_name', models.CharField(max_length=255, null=True, blank=True)),
                ('extra_data', django.contrib.postgres.fields.hstore.HStoreField(default={})),
                ('folder', models.CharField(max_length=4096)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='FileSetMetaData',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('extra_metadata', django.contrib.postgres.fields.hstore.HStoreField(default={})),
                ('keywords', django.contrib.postgres.fields.ArrayField(default=[], base_field=models.CharField(max_length=100, null=True, blank=True), size=None)),
                ('is_dirty', models.BooleanField(default=False)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='genericlogicalfile',
            name='resource',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='hs_composite_resource.CompositeResource'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='geofeaturelogicalfile',
            name='resource',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='hs_composite_resource.CompositeResource'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='georasterlogicalfile',
            name='resource',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='hs_composite_resource.CompositeResource'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='netcdflogicalfile',
            name='resource',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='hs_composite_resource.CompositeResource'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='reftimeserieslogicalfile',
            name='resource',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='hs_composite_resource.CompositeResource'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='timeserieslogicalfile',
            name='resource',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='hs_composite_resource.CompositeResource'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='filesetlogicalfile',
            name='metadata',
            field=models.OneToOneField(related_name='logical_file', on_delete=models.CASCADE, to='hs_file_types.FileSetMetaData'),
        ),
        migrations.AddField(
            model_name='filesetlogicalfile',
            name='resource',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='hs_composite_resource.CompositeResource'),
        ),
    ]
