# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('theme', '0008_auto_20170622_2141'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='highest_degree_completed',
            field=models.CharField(
                help_text=b'e.g. High School, Associate, Bachelors, Masters, Ph.D., Postdoc, other',
                max_length=1024,
                null=True,
                blank=True,
                choices=[
                    (b'high_school', b'High School Diploma'),
                    (b'associates', b'Associate Degree'),
                    (b'bachelors', b'Bachelors Degree'),
                    (b'masters', b'Masters Degree'),
                    (b'doctorate', b'Doctorate / Postdoc')
                ]
            ),
        )
    ]
