# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('hs_app_timeseries', '0002_auto_20150310_1927'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='timeseriesresource',
            options={'ordering': ('_order',), 'verbose_name': 'Time Series'},
        ),
        migrations.AlterField(
            model_name='timeseriesresource',
            name='owners',
            field=models.ManyToManyField(help_text=b'The person who has total ownership of the resource', related_name='owns_hs_app_timeseries_timeseriesresource', to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
    ]
