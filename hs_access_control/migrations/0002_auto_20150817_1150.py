# -*- coding: utf-8 -*-


from django.db import models, migrations
from django.contrib.auth.models import User
from hs_access_control.models import UserAccess


def migrate_users(apps, schema_editor):
    # create a 'UserAccess' record for each existing user - needed for the new access control to work
    UserAccess.objects.all().delete()
    for u in User.objects.all():
        ua = UserAccess(user=u)
        ua.save()


def undo_migrate_users(apps, schema_editor):
    # delete all 'UserAccess' records
    UserAccess.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('hs_access_control', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(code=migrate_users, reverse_code=undo_migrate_users),
    ]
