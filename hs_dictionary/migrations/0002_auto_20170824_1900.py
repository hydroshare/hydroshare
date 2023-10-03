# -*- coding: utf-8 -*-


import csv
import os

from django.db import migrations, models


def forwards(apps, schema_editor):
    University = apps.get_model('hs_dictionary', 'University')
    with open(os.path.dirname(__file__) + "/world-universities.csv") as f:
        reader = csv.reader(f)
        for i, line in enumerate(reader):
            University.objects.create(
                name=line[1],
                country_code=line[0],
                url=line[2]
            )


def backwards(apps, schema_editor):
    University = apps.get_model('hs_dictionary', 'University')
    University.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('hs_dictionary', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards)
    ]
