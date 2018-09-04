# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hs_explore', '0016_recommendedresource_rec_type'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='userpreferences',
            name='pref_type',
        ),
        migrations.AddField(
            model_name='userpreftopair',
            name='pref_type',
            field=models.CharField(max_length=10, null=True, choices=[(b'Ownership', b'Ownership'), (b'Propensity', b'Propensity')]),
        ),
        migrations.AlterUniqueTogether(
            name='recommendedresource',
            unique_together=set([('user', 'candidate_resource', 'rec_type')]),
        ),
        migrations.AlterUniqueTogether(
            name='userpreftopair',
            unique_together=set([('user_pref', 'pair', 'pref_type')]),
        ),
    ]
