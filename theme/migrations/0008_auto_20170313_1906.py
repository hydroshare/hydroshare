# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('theme', '0007_auto_20170310_2111'),
    ]

    operations = [
        migrations.AddField(
            model_name='quotamessage',
            name='soft_limit_percent',
            field=models.IntegerField(default=90),
        ),
        migrations.AlterField(
            model_name='userquota',
            name='user',
            field=models.ForeignKey(related_query_name=b'quotas', related_name='quotas', editable=False, to=settings.AUTH_USER_MODEL),
        ),
    ]
