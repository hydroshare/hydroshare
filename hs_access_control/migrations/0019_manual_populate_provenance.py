# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import migrations


def populate_provenance(apps, schema_editor):
    """
    Remove extra records from privileges tables

    This change adds a matching provenance record for each record in the corresponding privilege.
    This enables undo for existing privileges.

    """
    UserResourcePrivilege = apps.get_model("hs_access_control", "UserResourcePrivilege")
    UserGroupPrivilege = apps.get_model("hs_access_control", "UserGroupPrivilege")
    GroupResourcePrivilege = apps.get_model("hs_access_control", "GroupResourcePrivilege")
    UserResourceProvenance = apps.get_model("hs_access_control", "UserResourceProvenance")
    UserGroupProvenance = apps.get_model("hs_access_control", "UserGroupProvenance")
    GroupResourceProvenance = apps.get_model("hs_access_control", "GroupResourceProvenance")

    # brute force addition of provenance records
    for r in GroupResourcePrivilege.objects.all():
        GroupResourceProvenance.objects.create(group=r.group,
                                               resource=r.resource,
                                               start=r.start,
                                               privilege=r.privilege,
                                               grantor=r.grantor,
                                               undone=False)

    for r in UserResourcePrivilege.objects.all():
        UserResourceProvenance.objects.create(user=r.user,
                                              resource=r.resource,
                                              start=r.start,
                                              privilege=r.privilege,
                                              grantor=r.grantor,
                                              undone=False)

    for r in UserGroupPrivilege.objects.all():
        UserGroupProvenance.objects.create(user=r.user,
                                           group=r.group,
                                           start=r.start,
                                           privilege=r.privilege,
                                           grantor=r.grantor,
                                           undone=False)


class Migration(migrations.Migration):

    dependencies = [
        ('hs_access_control', '0018_auto_tune_provenance'),
    ]

    operations = [
        migrations.RunPython(populate_provenance),
    ]
