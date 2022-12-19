# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("hs_access_control", "0016_auto_enforce_constraints"),
    ]

    operations = [
        migrations.AddField(
            model_name="groupaccess",
            name="auto_approve",
            field=models.BooleanField(
                default=False,
                help_text="whether group can be auto approved",
                editable=False,
            ),
        ),
    ]
