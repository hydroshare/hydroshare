# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hs_app_netCDF', '0004_auto_20160921_2320'),
    ]

    operations = [
        migrations.AddField(
            model_name='originalcoverage',
            name='datum',
            field=models.CharField(max_length=300, blank=True),
        ),
        migrations.AlterField(
            model_name='originalcoverage',
            name='projection_string_type',
            field=models.CharField(max_length=20, null=True, choices=[('', '---------'), ('WKT Projection', 'WKT Projection'), ('Proj4 String', 'Proj4 String')]),
        ),
    ]
