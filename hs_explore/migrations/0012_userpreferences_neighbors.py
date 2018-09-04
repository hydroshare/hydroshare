# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('hs_explore', '0011_userpreferences_interested_resources'),
    ]

    operations = [
        migrations.AddField(
            model_name='userpreferences',
            name='neighbors',
            field=models.ManyToManyField(related_name='nearest_neighbors', editable=False, to=settings.AUTH_USER_MODEL),
        ),
    ]
