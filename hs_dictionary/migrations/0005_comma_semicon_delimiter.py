# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations
from theme.models import UserProfile
from django.db.models import F, Func, Value


def backwards(apps, schema_editor):
    UserProfile.objects.filter(organization__icontains=',').update(
        organization=Func(
            F('organization'),
            Value(';'), Value(','),
            function='replace',
        )
    )


def forwards(apps, schema_editor):
    UserProfile.objects.filter(organization__icontains=',').update(
        organization=Func(
            F('organization'),
            Value(','), Value(';'),
            function='replace',
        )
    )


class Migration(migrations.Migration):
    dependencies = [
        ('hs_dictionary', '0004_merge'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards)
    ]
