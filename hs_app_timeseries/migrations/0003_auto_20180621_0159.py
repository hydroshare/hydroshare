# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hs_app_timeseries', '0002_auto_20170602_2007'),
    ]

    operations = [
        migrations.AlterField(
            model_name='processinglevel',
            name='processing_level_code',
            field=models.CharField(max_length=50),
        ),
    ]
