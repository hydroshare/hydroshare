# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ("hs_core", "0005_auto_20150910_0233"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="genericresource",
            options={"ordering": ("_order",), "verbose_name": "Generic"},
        ),
    ]
