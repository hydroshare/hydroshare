# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations
from theme.models import UserProfile
from django.db.models import F, Func, Value


class Migration(migrations.Migration):
    dependencies = [

    ]

    operations = [
        UserProfile.objects.filter(organization__icontains=',').update(
            organization=Func(
                F('organization'),
                Value(','), Value(';'),
                function='replace',
            )
        )

    ]
