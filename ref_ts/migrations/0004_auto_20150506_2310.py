# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('ref_ts', '0003_referenceurl'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='reftimeseries',
            options={'ordering': ('_order',), 'verbose_name': 'HIS Referenced Time Series'},
        ),
        migrations.AlterField(
            model_name='reftimeseries',
            name='owners',
            field=models.ManyToManyField(help_text=b'The person who has total ownership of the resource', related_name='owns_ref_ts_reftimeseries', to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
    ]
