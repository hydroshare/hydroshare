# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("hs_file_types", "0006_reftimeseriesfilemetadata_abstract"),
    ]

    operations = [
        migrations.AddField(
            model_name="timeseriesfilemetadata",
            name="abstract",
            field=models.TextField(null=True, blank=True),
        ),
    ]
