# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hs_app_timeseries', '0003_auto_20180621_0159'),
    ]

    operations = [
        migrations.AlterField(
            model_name='site',
            name='site_name',
            field=models.CharField(max_length=255, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='timeseriesresult',
            name='status',
            field=models.CharField(max_length=255, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='variable',
            name='variable_code',
            field=models.CharField(max_length=50),
        ),
    ]
