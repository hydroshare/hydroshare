# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import migrations, models
# from django.contrib.auth.models import User, Group


def remove_extra_privileges(apps, schema_editor):
    User = apps.get_model("auth", "User")
    Group = apps.get_model("auth", "Group")
    BaseResource = apps.get_model("hs_core", "BaseResource")
    UserResourcePrivilege = apps.get_model("hs_access_control", "UserResourcePrivilege")
    UserGroupPrivilege = apps.get_model("hs_access_control", "UserGroupPrivilege")
    GroupResourcePrivilege = apps.get_model("hs_access_control", "GroupResourcePrivilege")

    # brute force removal of offending records.
    for u in User.objects.all():
        for r in BaseResource.objects.all():
            records = UserResourcePrivilege.objects.filter(user=u, resource=r)
            if records.count() > 1:  # do nothing if there are no duplicates
                # determine the lowest privilege number
                min = records.aggregate(models.Min('privilege'))
                min_privilege = min['privilege__min']
                # of records with this number, select the record with maximum timestamp.
                # This determines the (last) grantor
                max = records.filter(privilege=min_privilege).aggregate(models.Max('start'))
                max_start = max['start__max']
                to_keep = records.filter(privilege=min_privilege, start=max_start)
                if to_keep.count() == 1:
                    to_delete = records.exclude(pk__in=to_keep)
                    UserResourcePrivilege.objects.delete(pk__in=to_delete)
                elif to_keep.count() > 1:  # unlikely that two records would have the same timestamp
                    kept = records[0]  # choose first one arbitrarily
                    to_delete = records.exclude(pk=kept)
                    UserResourcePrivilege.objects.delete(pk__in=to_delete)

    for u in User.objects.all():
        for g in Group.objects.all():
            
            records = UserGroupPrivilege.objects.filter(user=u, group=g)
            if records.count() > 1:  # do nothing if there are no duplicates
                # determine the lowest privilege number
                min = records.aggregate(models.Min('privilege'))
                min_privilege = min['privilege__min']
                # of records with this number, select the record with maximum timestamp.
                # This determines the (last) grantor
                max = records.filter(privilege=min_privilege).aggregate(models.Max('start'))
                max_start = max['start__max']
                to_keep = records.filter(privilege=min_privilege, start=max_start)
                if to_keep.count() == 1:
                    to_delete = records.exclude(pk__in=to_keep)
                    UserGroupPrivilege.objects.delete(pk__in=to_delete)
                elif to_keep.count() > 1:  # unlikely that two records would have the same timestamp
                    kept = records[0]  # choose first one arbitrarily
                    to_delete = records.exclude(pk=kept)
                    UserGroupPrivilege.objects.delete(pk__in=to_delete)

    for g in Group.objects.all():
        for r in BaseResource.objects.all():
            records = GroupResourcePrivilege.objects.filter(group=g, resource=r)
            if records.count() > 1:  # do nothing if there are no duplicates
                # determine the lowest privilege number
                min = records.aggregate(models.Min('privilege'))
                min_privilege = min['privilege__min']
                # of records with this number, select the record with maximum timestamp.
                # This determines the (last) grantor
                max = records.filter(privilege=min_privilege).aggregate(models.Max('start'))
                max_start = max['start__max']
                to_keep = records.filter(privilege=min_privilege, start=max_start)
                if to_keep.count() == 1:
                    to_delete = records.exclude(pk__in=to_keep)
                    GroupResourcePrivilege.objects.delete(pk__in=to_delete)
                elif to_keep.count() > 1:  # unlikely that two records would have the same timestamp
                    kept = records[0]  # choose first one arbitrarily
                    to_delete = records.exclude(pk=kept)
                    GroupResourcePrivilege.objects.delete(pk__in=to_delete)


class Migration(migrations.Migration):

    dependencies = [
        ('hs_access_control', '0014_auto_20160424_1628'),
    ]

    operations = [
        migrations.RunPython(remove_extra_privileges),
    ]
