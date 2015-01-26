# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hs_geo_raster_resource', '0003_auto_20150123_2044'),
    ]

    operations = [
        migrations.RenameField(
            model_name='bandinformation',
            old_name='bandName',
            new_name='name',
        ),
    ]
