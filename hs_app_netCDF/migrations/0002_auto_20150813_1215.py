# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hs_app_netCDF', '0001_initial'),
    ]

    operations = [
        migrations.DeleteModel('NetcdfResource'),
    ]
