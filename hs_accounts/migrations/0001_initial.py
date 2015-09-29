 # -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [

        ('theme', '0001_initial'),

    ]

    operations = [

        migrations.RunSQL(sql=

            "SELECT * INTO hs_accounts_userprofile FROM theme_userprofile"),

    ]

