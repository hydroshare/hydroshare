# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("hs_core", "0037_auto_20180209_0309"),
    ]

    operations = [
        migrations.AlterIndexTogether(
            name="resourcefile",
            index_together=set(
                [("object_id", "resource_file"), ("object_id", "fed_resource_file")]
            ),
        ),
    ]
