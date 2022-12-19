# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("hs_tracking", "0002_auto_20160406_1244"),
    ]

    operations = [
        migrations.AlterField(
            model_name="variable",
            name="type",
            field=models.IntegerField(
                choices=[
                    (0, "Integer"),
                    (1, "Floating Point"),
                    (2, "Text"),
                    (3, "Flag"),
                    (4, "None"),
                ]
            ),
        ),
    ]
