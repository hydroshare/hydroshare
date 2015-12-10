# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('hs_labels', '0004_auto_20151209_2232'),
    ]

    operations = [
        migrations.AlterField(
            model_name='resourcelabels',
            name='resource',
            field=models.OneToOneField(related_query_name=b'rlabels', related_name='rlabels', null=True, editable=False, to='hs_core.BaseResource'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='userlabels',
            name='user',
            field=models.OneToOneField(related_query_name=b'ulabels', related_name='ulabels', null=True, editable=False, to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='userresourcelabels',
            name='rlabels',
            field=models.ForeignKey(related_name='rl2url', editable=False, to='hs_labels.ResourceLabels', help_text=b'resource to which a label applies'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='userresourcelabels',
            name='ulabels',
            field=models.ForeignKey(related_name='ul2url', editable=False, to='hs_labels.UserLabels', help_text=b'user assigning a label'),
            preserve_default=True,
        ),
    ]
