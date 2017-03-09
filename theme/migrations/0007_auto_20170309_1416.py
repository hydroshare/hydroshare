# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('theme', '0006_auto_20170228_2008'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='userquota',
            options={'verbose_name': 'User quota', 'verbose_name_plural': 'User quotas'},
        ),
        migrations.RenameField(
            model_name='userquota',
            old_name='value',
            new_name='allocated_value',
        ),
        migrations.AddField(
            model_name='userquota',
            name='used_value',
            field=models.BigIntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='userquota',
            name='user',
            field=models.ForeignKey(related_name='quotas', to=settings.AUTH_USER_MODEL),
        ),
    ]
