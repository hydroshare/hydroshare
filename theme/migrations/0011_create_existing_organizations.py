# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


def forward(apps, schema_editor):
    UserProfile = apps.get_model('theme', 'UserProfile')
    Organization = apps.get_model('theme', 'Organization')
    for profile in UserProfile.objects.filter(organization__isnull=False):
        org = profile.organization.strip()
        if org:
            org, _ = Organization.objects.get_or_create(name=org)
            profile._organization = org
            profile.save()


def reverse(apps, schema_editor):
    UserProfile = apps.get_model('theme', 'UserProfile')
    for profile in UserProfile.objects.filter(_organization__isnull=False):
        profile.organization = profile._organization.name
        profile.save()


class Migration(migrations.Migration):

    dependencies = [
        ('theme', '0010_add_organization'),
    ]

    operations = [
        migrations.RunPython(forward, reverse),
    ]
