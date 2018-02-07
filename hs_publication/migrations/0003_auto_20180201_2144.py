# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hs_publication', '0002_auto_20180201_2058'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='publicationqueue',
            options={'verbose_name': 'Publication Queue Item', 'verbose_name_plural': 'Publication Queue Items'},
        ),
        migrations.RemoveField(
            model_name='publicationqueue',
            name='user',
        ),
        migrations.AlterField(
            model_name='publicationqueue',
            name='status',
            field=models.CharField(default=b'pending', max_length=8, choices=[(b'pending', b'Pending Approval'), (b'approved', b'Publication Approved'), (b'denied', b'Publication Request Denied')]),
        ),
    ]
