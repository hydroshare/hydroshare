# -*- coding: utf-8 -*-


from django.db import models, migrations
from django.conf import settings
import hs_core.models


class Migration(migrations.Migration):

    dependencies = [
        ("auth", "0001_initial"),
        ("pages", "__first__"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("contenttypes", "0001_initial"),
        ("hs_core", "0002_genericresource_resource_type"),
    ]

    operations = [
        migrations.RenameModel("GenericResource", "BaseResource"),
    ]
