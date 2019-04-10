# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import csv
import os

from django.db import migrations, models

from hs_dictionary.models import University


def forwards(apps, schema_editor):
    with open(os.path.dirname(__file__) + "/world-universities.csv") as f:
        reader = csv.reader(f)
        for i, line in enumerate(reader):
            University.objects.create(
                name=line[1],
                country_code=line[0],
                url=line[2]
            )


def backwards(apps, schema_editor):
    University.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('hs_dictionary', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards)
    ]
