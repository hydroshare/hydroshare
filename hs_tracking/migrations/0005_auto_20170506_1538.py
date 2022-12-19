# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("hs_tracking", "0004_auto_20161010_1402"),
    ]

    operations = [
        migrations.AlterField(
            model_name="variable",
            name="value",
            field=models.TextField(),
        ),
    ]
