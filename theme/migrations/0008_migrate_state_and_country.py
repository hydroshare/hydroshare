# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django_countries import countries
from localflavor.us.us_states import STATES_NORMALIZED, STATE_CHOICES


def forward(apps, schema_editor):
    UserProfile = apps.get_model('theme', 'UserProfile')
    for profile in UserProfile.objects.all():
        if profile.country not in ('Unspecified', '', None):
            from_name = countries.by_name(profile.country)
            if from_name:
                code = from_name
            else:
                code = countries.alpha2(profile.country)

            profile.new_country = code

        if profile.state not in ('Unspecified', '', None):
            profile.new_state = STATES_NORMALIZED.get(profile.state.strip().lower(), '')

        profile.save()


def reverse(apps, schema_editor):
    UserProfile = apps.get_model('theme', 'UserProfile')
    states = dict(STATE_CHOICES)
    for profile in UserProfile.objects.all():
        profile.country = profile.new_country
        profile.state = states.get(profile.new_state, '')
        profile.save()


class Migration(migrations.Migration):

    dependencies = [
        ('theme', '0007_add_state_and_country_fields'),
    ]

    operations = [
        migrations.RunPython(forward, reverse),
    ]
