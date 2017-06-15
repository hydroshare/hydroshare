# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('theme', '0007_auto_20170427_1553'),
    ]

    operations = [
        migrations.AlterField(
            model_name='quotamessage',
            name='enforce_content_prepend',
            field=models.TextField(default=b'Your action was refused because you have exceeded your quota. Your quota for HydroShare resources is {allocated}{unit} in {zone} zone. You currently have resources that consume {used}{unit}, {percent}% of your quota. '),
        ),
    ]
