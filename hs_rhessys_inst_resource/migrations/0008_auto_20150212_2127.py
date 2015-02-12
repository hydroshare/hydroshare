# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('hs_rhessys_inst_resource', '0007_auto_20150211_1620'),
    ]

    operations = [
        migrations.AlterField(
            model_name='modelrun',
            name='date_started',
            field=models.DateTimeField(default=datetime.datetime(2015, 2, 12, 21, 27, 35, 948672, tzinfo=utc), auto_now_add=True),
            preserve_default=False,
        ),
    ]
