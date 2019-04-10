# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models

# Merge two concurrent changes to access control. 


class Migration(migrations.Migration):

    dependencies = [
        ('hs_access_control', '0019_manual_populate_provenance'),
        ('hs_access_control', '0017_groupaccess_auto_approve'),
    ]

    operations = [
    ]
