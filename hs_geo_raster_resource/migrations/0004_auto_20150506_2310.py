# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('hs_geo_raster_resource', '0003_auto_20150313_2136'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='rasterresource',
            options={'ordering': ('_order',), 'verbose_name': 'Geographic Raster'},
        ),
        migrations.AlterField(
            model_name='rasterresource',
            name='owners',
            field=models.ManyToManyField(help_text=b'The person who has total ownership of the resource', related_name='owns_hs_geo_raster_resource_rasterresource', to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
    ]
