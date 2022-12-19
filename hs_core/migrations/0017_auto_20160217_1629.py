# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ("hs_core", "0016_merge"),
    ]

    operations = [
        migrations.AlterField(
            model_name="relation",
            name="type",
            field=models.CharField(
                max_length=100,
                choices=[
                    ("isHostedBy", "Hosted By"),
                    ("isCopiedFrom", "Copied From"),
                    ("isPartOf", "Part Of"),
                    ("isExecutedBy", "Executed By"),
                    ("isCreatedBy", "Created By"),
                    ("isVersionOf", "Version Of"),
                    ("isReplacedBy", "Replaced By"),
                    ("isDataFor", "Data For"),
                    ("cites", "Cites"),
                    ("isDescribedBy", "Described By"),
                ],
            ),
            preserve_default=True,
        ),
    ]
