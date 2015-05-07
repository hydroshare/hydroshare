# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('hs_core', '0002_auto_20150310_1927'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='genericresource',
            options={'ordering': ('_order',), 'verbose_name': 'Generic'},
        ),
        migrations.AlterField(
            model_name='genericresource',
            name='owners',
            field=models.ManyToManyField(help_text=b'The person who has total ownership of the resource', related_name='owns_hs_core_genericresource', to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
    ]
