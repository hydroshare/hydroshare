# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hs_file_types', '0002_auto_20170128_2314'),
    ]

    operations = [
        migrations.CreateModel(
            name='BaseLogicalFile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('logical_file_type', models.CharField(default=b'Generic', max_length=100)),
                ('dataset_name', models.CharField(max_length=255, null=True, blank=True)),
                ('metadata', models.OneToOneField(related_name='logical_file', to='hs_file_types.BaseFileMetaData')),
            ],
        ),
        migrations.RemoveField(
            model_name='netcdflogicalfile',
            name='metadata',
        ),
        migrations.DeleteModel(
            name='NetCDFLogicalFile',
        ),
        migrations.CreateModel(
            name='NetCDFLogicalFile',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('hs_file_types.baselogicalfile',),
        ),
    ]
