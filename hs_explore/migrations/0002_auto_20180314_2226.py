# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('hs_explore', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='recommend',
            name='relevance',
            field=models.FloatField(default=0.0, editable=False),
        ),
        migrations.AlterField(
            model_name='recommend',
            name='resource',
            field=models.ForeignKey(editable=False, to='hs_core.BaseResource'),
        ),
        migrations.AlterField(
            model_name='recommend',
            name='state',
            field=models.IntegerField(default=1, editable=False, choices=[(1, b'New'), (2, b'Viewed'), (3, b'Approved'), (4, b'Dismissed')]),
        ),
        migrations.AlterField(
            model_name='recommend',
            name='user',
            field=models.ForeignKey(editable=False, to=settings.AUTH_USER_MODEL),
        ),
    ]
