# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('hs_explore', '0017_auto_20180724_1632'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userpreferences',
            name='user',
            field=models.OneToOneField(editable=False, to=settings.AUTH_USER_MODEL),
        ),
    ]
