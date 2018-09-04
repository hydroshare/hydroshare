# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hs_explore', '0007_auto_20180702_0238'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserPrefToPair',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('pair', models.ForeignKey(editable=False, to='hs_explore.KeyValuePair')),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='grouppreferences',
            unique_together=set([]),
        ),
        migrations.RemoveField(
            model_name='grouppreferences',
            name='group',
        ),
        migrations.AlterUniqueTogether(
            name='userpreferences',
            unique_together=set([]),
        ),
        migrations.DeleteModel(
            name='GroupPreferences',
        ),
        migrations.AddField(
            model_name='userpreftopair',
            name='user_pref',
            field=models.ForeignKey(editable=False, to='hs_explore.UserPreferences'),
        ),
        migrations.RemoveField(
            model_name='userpreferences',
            name='preferences',
        ),
        migrations.AddField(
            model_name='userpreferences',
            name='preferences',
            field=models.ManyToManyField(related_name='for_user_pref', editable=False, through='hs_explore.UserPrefToPair', to='hs_explore.KeyValuePair'),
        ),
        migrations.AlterUniqueTogether(
            name='userpreftopair',
            unique_together=set([('user_pref', 'pair')]),
        ),
    ]
