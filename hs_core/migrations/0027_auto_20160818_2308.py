# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("hs_core", "0026_merge"),
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
                    ("hasPart", "Has Part"),
                    ("isExecutedBy", "Executed By"),
                    ("isCreatedBy", "Created By"),
                    ("isVersionOf", "Version Of"),
                    ("isReplacedBy", "Replaced By"),
                    ("isDataFor", "Data For"),
                    ("cites", "Cites"),
                    ("isDescribedBy", "Described By"),
                ],
            ),
        ),
        migrations.AlterUniqueTogether(
            name="relation",
            unique_together=set([]),
        ),
    ]
