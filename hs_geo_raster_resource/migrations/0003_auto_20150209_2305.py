# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hs_geo_raster_resource', '0002_auto_20150205_2145'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='cellinformation',
            unique_together=set([('content_type', 'object_id')]),
        ),
    ]
