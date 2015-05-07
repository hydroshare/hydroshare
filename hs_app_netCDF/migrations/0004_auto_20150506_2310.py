# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('hs_app_netCDF', '0003_auto_20150415_1751'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='netcdfresource',
            options={'ordering': ('_order',), 'verbose_name': 'Multidimensional (NetCDF)'},
        ),
        migrations.AlterField(
            model_name='netcdfresource',
            name='owners',
            field=models.ManyToManyField(help_text=b'The person who has total ownership of the resource', related_name='owns_hs_app_netcdf_netcdfresource', to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='variable',
            name='descriptive_name',
            field=models.CharField(max_length=100, null=True, verbose_name=b'long name', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='variable',
            name='method',
            field=models.TextField(null=True, verbose_name=b'comment', blank=True),
            preserve_default=True,
        ),
    ]
