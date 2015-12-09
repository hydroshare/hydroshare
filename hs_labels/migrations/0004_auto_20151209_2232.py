# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('hs_labels', '0003_auto_20151209_0123'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserStoredLabels',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('label', models.TextField(help_text=b'label to be stored by user')),
                ('ulabels', models.ForeignKey(related_name='ul2usl', to='hs_labels.UserLabels', help_text=b'user who stored the label', null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AlterField(
            model_name='resourcelabels',
            name='resource',
            field=models.OneToOneField(related_query_name=b'rlabels', related_name='rlabels', editable=False, to='hs_core.BaseResource'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='userlabels',
            name='user',
            field=models.OneToOneField(related_query_name=b'ulabels', related_name='ulabels', editable=False, to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='userresourcelabels',
            name='kind',
            field=models.IntegerField(default=1, editable=False, choices=[(1, b'Label'), (2, b'Folder'), (3, b'Favorite'), (4, b'Mine')]),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='userresourcelabels',
            name='ulabels',
            field=models.ForeignKey(related_name='ul2url', editable=False, to='hs_labels.UserLabels', help_text=b'user assigning a label', null=True),
            preserve_default=True,
        ),
    ]
