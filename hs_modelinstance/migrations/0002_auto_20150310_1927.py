# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hs_modelinstance', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='modelinstanceresource',
            name='rating_average',
            field=models.FloatField(default=0, editable=False),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='modelinstanceresource',
            name='rating_count',
            field=models.IntegerField(default=0, editable=False),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='modelinstanceresource',
            name='rating_sum',
            field=models.IntegerField(default=0, editable=False),
            preserve_default=True,
        ),
    ]
