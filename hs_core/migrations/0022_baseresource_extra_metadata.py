# -*- coding: utf-8 -*-


from django.db import migrations, models
import django.contrib.postgres.fields.hstore


class Migration(migrations.Migration):

    dependencies = [
        ("hs_core", "0021_hstore_extension"),
    ]

    operations = [
        migrations.AddField(
            model_name="baseresource",
            name="extra_metadata",
            field=django.contrib.postgres.fields.hstore.HStoreField(default={}),
        ),
    ]
