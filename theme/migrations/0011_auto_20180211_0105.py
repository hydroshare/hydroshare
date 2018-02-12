# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


def migrate_user_quota_default_zone_name(apps, schema_editor):
    """
    data migration that migrate hydroshare_internal zone name to hydroshare zone name for
    all rows in UserQuota model
    """
    UserQuota = apps.get_model("theme", "UserQuota")
    for uq in UserQuota.objects.all():
        uq.zone = 'hydroshare'
        uq.save()


class Migration(migrations.Migration):

    dependencies = [
        ('theme', '0010_auto_20180207_1845'),
    ]

    operations = [
        migrations.RunPython(migrate_user_quota_default_zone_name),
    ]
