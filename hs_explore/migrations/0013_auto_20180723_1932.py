# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('hs_explore', '0012_userpreferences_neighbors'),
    ]

    operations = [
        migrations.RenameField(
            model_name='userpreferences',
            old_name='interested_resources',
            new_name='interacted_resources',
        ),
        migrations.AddField(
            model_name='userpreferences',
            name='pref_type',
            field=models.CharField(blank=True, max_length=10, null=True, choices=[(b'Ownership', b'Ownership'), (b'Propensity', b'Propensity')]),
        ),
        migrations.AddField(
            model_name='userpreftopair',
            name='state',
            field=models.CharField(default=b'Seen', max_length=8, choices=[(b'Seen', b'Seen'), (b'Rejected', b'Rejected')]),
        ),
        migrations.AlterField(
            model_name='userpreferences',
            name='user',
            field=models.OneToOneField(editable=False, to=settings.AUTH_USER_MODEL),
        ),
    ]
