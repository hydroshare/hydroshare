# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hs_labels', '0002_custom_migration'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userresourcelabels',
            name='kind',
            field=models.IntegerField(default=1, editable=False, choices=[(1, b'Label'), (2, b'Folder'), (3, b'Favorite'), (4, b'Mine'), (5, b'Saved Label')]),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='userresourcelabels',
            name='rlabels',
            field=models.ForeignKey(related_name='rl2url', editable=False, to='hs_labels.ResourceLabels', help_text=b'resource to which a label applies', null=True),
            preserve_default=True,
        ),
    ]
