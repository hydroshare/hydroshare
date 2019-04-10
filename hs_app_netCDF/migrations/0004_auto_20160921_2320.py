# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hs_app_netCDF', '0003_netcdfresource'),
    ]

    operations = [
        migrations.AlterField(
            model_name='variable',
            name='descriptive_name',
            field=models.CharField(max_length=1000, null=True, verbose_name=b'long name', blank=True),
        ),
        migrations.AlterField(
            model_name='variable',
            name='missing_value',
            field=models.CharField(max_length=1000, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='variable',
            name='name',
            field=models.CharField(max_length=1000),
        ),
        migrations.AlterField(
            model_name='variable',
            name='shape',
            field=models.CharField(max_length=1000),
        ),
        migrations.AlterField(
            model_name='variable',
            name='type',
            field=models.CharField(max_length=1000, choices=[(b'Char', b'Char'), (b'Byte', b'Byte'), (b'Short', b'Short'), (b'Int', b'Int'), (b'Float', b'Float'), (b'Double', b'Double'), (b'Int64', b'Int64'), (b'Unsigned Byte', b'Unsigned Byte'), (b'Unsigned Short', b'Unsigned Short'), (b'Unsigned Int', b'Unsigned Int'), (b'Unsigned Int64', b'Unsigned Int64'), (b'String', b'String'), (b'User Defined Type', b'User Defined Type'), (b'Unknown', b'Unknown')]),
        ),
        migrations.AlterField(
            model_name='variable',
            name='unit',
            field=models.CharField(max_length=1000),
        ),
    ]
