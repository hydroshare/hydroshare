# -*- coding: utf-8 -*-


from django.db import models, migrations
from django.conf import settings
import hs_core.models


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0001_initial'),
        ('sites', '0001_initial'),
        ('pages', '__first__'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('contenttypes', '0001_initial'),
        ('hs_core', '0004_auto_20150721_1125'),
        ('hs_tools_resource', '0002_auto_20150724_1422'),
    ]

    operations = [
        migrations.DeleteModel("ToolResource"),
        migrations.CreateModel(
            name='ToolResource',
            fields=[
            ],
            options={
                'ordering': ('_order',),
                'verbose_name': 'Tool Resource',
                'proxy': True,
            },
            bases=('hs_core.baseresource',),
        ),
    ]
