# -*- coding: utf-8 -*-


from django.db import migrations
from django.db.models import F, Func, Value


def backwards(apps, schema_editor):
    UserProfile = apps.get_model('theme', 'UserProfile')
    UserProfile.objects.filter(organization__icontains=',').update(
        organization=Func(
            F('organization'),
            Value(';'), Value(','),
            function='replace',
        )
    )


def forwards(apps, schema_editor):
    UserProfile = apps.get_model('theme', 'UserProfile')
    UserProfile.objects.filter(organization__icontains=',').update(
        organization=Func(
            F('organization'),
            Value(','), Value(';'),
            function='replace',
        )
    )


class Migration(migrations.Migration):
    dependencies = [
        ('theme', '0013_auto_20180222_1700'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards)
    ]
