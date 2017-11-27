# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hs_file_types', '0006_reftimeseriesfilemetadata_abstract'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='genericlogicalfile',
            options={'verbose_name': 'Generic File Type'},
        ),
        migrations.AlterModelOptions(
            name='geofeaturelogicalfile',
            options={'verbose_name': 'Geographic Feature File Type'},
        ),
        migrations.AlterModelOptions(
            name='georasterlogicalfile',
            options={'verbose_name': 'Geographic Raster File Type'},
        ),
        migrations.AlterModelOptions(
            name='netcdflogicalfile',
            options={'verbose_name': 'Multidimensional File Type'},
        ),
        migrations.AlterModelOptions(
            name='reftimeserieslogicalfile',
            options={'verbose_name': 'Reference Timeseries File Type'},
        ),
    ]
