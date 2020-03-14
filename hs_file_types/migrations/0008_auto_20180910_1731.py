# -*- coding: utf-8 -*-


from django.db import migrations, models
import django.contrib.postgres.fields.hstore


class Migration(migrations.Migration):

    dependencies = [
        ('hs_file_types', '0007_timeseriesfilemetadata_abstract'),
    ]

    operations = [
        migrations.AddField(
            model_name='genericlogicalfile',
            name='extra_data',
            field=django.contrib.postgres.fields.hstore.HStoreField(default={}),
        ),
        migrations.AddField(
            model_name='geofeaturelogicalfile',
            name='extra_data',
            field=django.contrib.postgres.fields.hstore.HStoreField(default={}),
        ),
        migrations.AddField(
            model_name='georasterlogicalfile',
            name='extra_data',
            field=django.contrib.postgres.fields.hstore.HStoreField(default={}),
        ),
        migrations.AddField(
            model_name='netcdflogicalfile',
            name='extra_data',
            field=django.contrib.postgres.fields.hstore.HStoreField(default={}),
        ),
        migrations.AddField(
            model_name='reftimeserieslogicalfile',
            name='extra_data',
            field=django.contrib.postgres.fields.hstore.HStoreField(default={}),
        ),
        migrations.AddField(
            model_name='timeserieslogicalfile',
            name='extra_data',
            field=django.contrib.postgres.fields.hstore.HStoreField(default={}),
        ),
    ]
