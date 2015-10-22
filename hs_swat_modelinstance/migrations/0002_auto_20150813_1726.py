# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hs_swat_modelinstance', '0001_initial'),
    ]

    operations = [
        migrations.DeleteModel('SWATModelInstanceResource'),
    ]
