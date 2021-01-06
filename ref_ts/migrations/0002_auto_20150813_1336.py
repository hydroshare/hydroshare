# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ref_ts', '0001_initial'),
    ]

    operations = [
        migrations.DeleteModel('RefTimeSeries'),
    ]
