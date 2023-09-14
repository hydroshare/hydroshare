# -*- coding: utf-8 -*-


from django.db import migrations
from django.contrib.auth.models import User


def migrate_user_quotas(apps, schema_editor):
    UserQuota = apps.get_model('theme', 'UserQuota')
    # create a UserQuota record for each existing user with default quota allocation values
    for u in User.objects.all():
        if not UserQuota.objects.filter(user=u).exists() and u.is_active and not u.is_superuser:
            uq = UserQuota.objects.create(user=u)
            uq.save()


def undo_migrate_user_quotas(apps, schema_editor):
    UserQuota = apps.get_model('theme', 'UserQuota')
    # delete all UserQuota records
    UserQuota.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('theme', '0005_userquota'),
    ]

    operations = [
        migrations.RunPython(code=migrate_user_quotas, reverse_code=undo_migrate_user_quotas),
    ]
