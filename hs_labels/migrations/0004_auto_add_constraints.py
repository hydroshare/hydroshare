# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('hs_labels', '0003_manual_delete_duplicates'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userstoredlabels',
            name='user',
            field=models.ForeignKey(related_name='ul2usl', to=settings.AUTH_USER_MODEL, help_text=b'user who stored the label'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='userresourceflags',
            unique_together=set([('user', 'resource', 'kind')]),
        ),
        migrations.AlterUniqueTogether(
            name='userresourcelabels',
            unique_together=set([('user', 'resource', 'label')]),
        ),
        migrations.AlterUniqueTogether(
            name='userstoredlabels',
            unique_together=set([('user', 'label')]),
        ),
    ]
