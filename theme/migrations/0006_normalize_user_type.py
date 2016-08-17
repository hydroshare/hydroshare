# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


def forwards(apps, schema_editor):
    UserProfile = apps.get_model('theme', 'UserProfile')

    for profile in UserProfile.objects.all():
        if profile.user_type not in ('',
                                     "University Faculty",
                                     "University Professional or Research Staff",
                                     "Post-Doctoral Fellow",
                                     "University Graduate Student",
                                     "University Undergraduate Student",
                                     "Commercial/Professional",
                                     "Government Official",
                                     "School Student Kindergarten to 12th Grade",
                                     "School Teacher Kindergarten to 12th Grade"):
            if profile.user_type is None:
                profile.user_type = ''
            elif profile.user_type == 'Unspecified':
                profile.user_type = ''
            else:
                profile.user_type_other = profile.user_type
                profile.user_type = 'Other'

            profile.save()


def reverse(apps, schema_editor):
    UserProfile = apps.get_model('theme', 'UserProfile')

    for profile in UserProfile.objects.filter(user_type='Other'):
        profile.user_type = profile.user_type_other
        profile.user_type_other = ''
        profile.save()


class Migration(migrations.Migration):

    dependencies = [
        ('theme', '0005_user_type_choices'),
    ]

    operations = [
        migrations.RunPython(forwards, reverse)
    ]
