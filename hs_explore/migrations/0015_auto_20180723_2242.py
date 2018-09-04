# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('hs_explore', '0014_auto_20180723_2108'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userpreferences',
            name='user',
            field=models.ForeignKey(editable=False, to=settings.AUTH_USER_MODEL),
        ),
    ]
